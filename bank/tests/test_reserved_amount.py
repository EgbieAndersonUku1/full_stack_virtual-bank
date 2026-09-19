"""
Tests for bank account reserved funds and overdraft calculations.

The tests cover:
- Default reserved amount.
- Available balance after funds are reserved.
- Accumulation of reserved amounts.
- Remaining overdraft capacity as reserved funds increase.
- Behaviour when overdraft is disabled.
- Default overdraft limits for newly created accounts.
"""


from decimal import Decimal

from django.test import TestCase
from django.conf import settings

from authentication.models import User
from bank.management.commands.seed_banks import BANK_SEED_DATA
from bank.models import Bank, BankAccount
from bank.services.bank_services import BankProvisioningService
from bank.services.transaction_services import TransactionService
from user_profile.models import UserProfile


from bank.services.funding_service import FundingService
from setup.services.service import AccountOnboardingService


bank_data = BANK_SEED_DATA[0]


USER_PROFILE_DATA_1 = {
    "first_name": "John",
    "last_name": "Smith",
    "city": "London",
    "postcode": "SW1A 1AA",
    "country": "GB",
}


USER_PROFILE_DATA_2 = {
    "first_name": "Jane",
    "last_name": "Smith",
    "city": "London",
    "postcode": "SW1A 1AA",
    "country": "GB",
}



USER_PROFILE_DATA_3 = {
    "first_name": "J",
    "last_name": "Smith",
    "city": "London",
    "postcode": "SW1A 1AA",
    "country": "GB",
}


class ReservedAmountTest(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.username_1 = "username_test_1"
        cls.username_2 = "username_test_2"
        cls.username_3 = "username_test_3"

        cls.user_1  = User.objects.create(username=cls.username_1, email="test_email1@test.com")
        cls.user_2  = User.objects.create(username=cls.username_2, email="test_email2@test.com")
        cls.user_3  = User.objects.create(username=cls.username_3, email="test_email3@test.com")

        # first bank created has overdraft functionalities
        BankProvisioningService.create_bank(BANK_SEED_DATA[0], source=Bank.Source.SEEDED)

        # Second bank account does not provide overdraft functionalities
        BankProvisioningService.create_bank(BANK_SEED_DATA[3], source=Bank.Source.SEEDED)

        cls.bank                   = Bank.objects.filter(offer_overdraft=Bank.OverDraftOptions.YES).first()
        cls.bank_with_no_overdraft = Bank.objects.filter(offer_overdraft=Bank.OverDraftOptions.NO).first()


        # onboard account 1
        AccountOnboardingService.complete_onboarding(user=cls.user_1,
                                                     bank=cls.bank,
                                                     profile_data=USER_PROFILE_DATA_1,
                                                     pin="1234"
                                                     )

        # onboard account 2
        AccountOnboardingService.complete_onboarding(user=cls.user_2,
                                                     bank=cls.bank,
                                                     profile_data=USER_PROFILE_DATA_2,
                                                     pin="1234"
                                                     )

        # onboard account 3
        AccountOnboardingService.complete_onboarding(user=cls.user_3,
                                                    bank=cls.bank_with_no_overdraft,
                                                    profile_data=USER_PROFILE_DATA_3,
                                                    pin="1234"
                                                             )


    def setUp(self):
        self.funding_amount = Decimal("1000")

        # user 1 will be the source account for her test
        FundingService.add_funds_to_current_account(amount=self.funding_amount, user=self.user_1)

        # user with overdraft
        self.user_profile            = UserProfile.get_profile_by_user(self.user_1)
        accounts                     = BankAccount.get_all_account_by_user_profile(user_profile=self.user_profile)
        self.source_current_account  = accounts[0]
        self.source_saving_account   = accounts[1]


    def test_bank_creation(self):
        EXPECTED_COUNT = 2
        BANK_NAME      = bank_data["name"]
        self.assertTrue(Bank.objects.filter(name=BANK_NAME).exists())
        self.assertEqual(Bank.objects.count(), EXPECTED_COUNT)

    def test_accounts_is_created(self):
        EXPECTED_COUNT = 6
        self.assertEqual(BankAccount.objects.count(), EXPECTED_COUNT, "Expected a count of six, i.e 3 current account and 3 saving accounts")

    def test_users_creation(self):

        EXPECTED_COUNT = 3
        self.assertTrue(User.objects.filter(username=self.username_1).exists(), "User 1 was not created")
        self.assertTrue(User.objects.filter(username=self.username_2).exists(), "User 2 was not created")
        self.assertTrue(User.objects.filter(username=self.username_3).exists(), "User 2 was not created")
        self.assertEqual(User.objects.count(), EXPECTED_COUNT, "Expected 2 users")

    def test_users_profiles_creation(self):

        EXPECTED_COUNT = 3
        user_profile_1_name = USER_PROFILE_DATA_1["first_name"]
        user_profile_2_name = USER_PROFILE_DATA_2["first_name"]
        user_profile_3_name = USER_PROFILE_DATA_2["first_name"]

        self.assertTrue(UserProfile.objects.filter(first_name=user_profile_1_name).exists(), "User 1 profile was not created")
        self.assertTrue(UserProfile.objects.filter(first_name=user_profile_2_name).exists(), "User 2 profile was not created")
        self.assertTrue(UserProfile.objects.filter(first_name=user_profile_3_name).exists(), "User 3 profile was not created")

        self.assertEqual(UserProfile.objects.count(), EXPECTED_COUNT, "Expected 3 users profiles")

    def test_if_source_account_is_funded(self):

        EXPECTED_AMOUNT   = Decimal("1000")
        self.assertEqual(self.source_current_account.balance, EXPECTED_AMOUNT, "Expected an amount of 1000")

    def test_if_overdraft_is_true(self):
        self.assertTrue(self.source_current_account.supports_overdraft, "Current Account should support overdraft")
        self.assertTrue(self.source_saving_account.supports_overdraft,  "Saving Account should support overdraft")

    def test_if_account_has_default_overdraft_limit_upon_creation(self):

        self.assertEqual(self.source_saving_account.overdraft_limit,
                        settings.DEFAULT_OVERDRAFT_LIMIT,
                        msg="Default overdraft limit is not set"
                        )

    def test_reserved_amount_is_zero_upon_creation(self):
        EXPECTED_AMOUNT = Decimal("0.00")

        self.assertEqual(self.source_current_account.reserved_amount,
                         EXPECTED_AMOUNT,
                         msg="Default reserved amount should be zero upon creation",
                        )

    def test_reserved_amount_and_overdraft_calculations(self):

        REMAINING_OVERDRAFT = Decimal("500")
        EXPECTED_BANK_BALANCE = Decimal("1000")

        # Test 1 -> £1,000 balance, £0 reserved → available £1,000 → remaining overdraft £500
        self.assertEqual(
            self.source_current_account.balance,
            self.source_current_account.available_balance,
            "Current account balance is not equal to the available balance"
        )

        self.assertEqual(
            self.source_current_account.reserved_amount,
            Decimal("0.00")
        )

        self.assertEqual(
            self.source_current_account.remaining_overdraft,
            REMAINING_OVERDRAFT,
            msg="Expected the remaining overdraft to be default amount"
        )

        # Test 2 -> £1,000 balance, £200 reserved → available £800 → remaining overdraft £500
        self.source_current_account.update_reserved_amount(Decimal("200"))  # reserve 200
        self.source_current_account.save()
        self.source_current_account.refresh_from_db()

        self.assertEqual(
            self.source_current_account.balance,
            EXPECTED_BANK_BALANCE,
            f"Bank balance should be {EXPECTED_BANK_BALANCE}"
        )

        self.assertEqual(
            self.source_current_account.reserved_amount,
            Decimal("200"),
            "Reserved should be 200"
        )

        self.assertEqual(
            self.source_current_account.available_balance,
            Decimal("800"),
            "Available balance should be 800"
        )

        self.assertEqual(
            self.source_current_account.remaining_overdraft,
            REMAINING_OVERDRAFT,
            msg="Expected the remaining overdraft to be default amount"
        )

        # Test 3 -> £1,000 balance, £1,200 reserved → available -£200 → remaining overdraft £300
        self.source_current_account.update_reserved_amount(Decimal("1000"))  # reserve is now 1200
        self.source_current_account.save()
        self.source_current_account.refresh_from_db()

        self.assertEqual(
            self.source_current_account.balance,
            EXPECTED_BANK_BALANCE,
            f"Bank balance should be {EXPECTED_BANK_BALANCE}"
        )

        self.assertEqual(
            self.source_current_account.reserved_amount,
            Decimal("1200"),
            "Reserved should be 1200"
        )

        self.assertEqual(
            self.source_current_account.available_balance,
            Decimal("-200"),
            "Available balance should be -200"
        )

        self.assertEqual(
            self.source_current_account.remaining_overdraft,
            Decimal("300"),
            msg="Expected the remaining overdraft to be 300"
        )

        # Test 4 -> £1,000 balance, £1,500 reserved → available -£500 → remaining overdraft £0
        self.source_current_account.update_reserved_amount(Decimal("300"))  # reserved 1500
        self.source_current_account.save()
        self.source_current_account.refresh_from_db()

        self.assertEqual(
            self.source_current_account.balance,
            EXPECTED_BANK_BALANCE,
            f"Bank balance should be {EXPECTED_BANK_BALANCE}"
        )

        self.assertEqual(
            self.source_current_account.reserved_amount,
            Decimal("1500"),
            "Reserved should be 1500"
        )

        self.assertEqual(
            self.source_current_account.available_balance,
            Decimal("-500"),
            "Available balance should be -500"
        )

        self.assertEqual(
            self.source_current_account.remaining_overdraft,
            Decimal("0"),
            msg="Expected the remaining overdraft to be 0"
        )

        # Test 5 -> £500 balance, £0 reserved, account has no overdraft functionality
        user_profile          = UserProfile.get_profile_by_user(self.user_3)
        no_overdraft_account  = BankAccount.get_all_account_by_user_profile(user_profile=user_profile)[0]

        no_overdraft_account.balance = Decimal("500.00")
        no_overdraft_account.save()
        no_overdraft_account.refresh_from_db()

        self.assertEqual(
            no_overdraft_account.balance,
            Decimal("500.00")
        )

        self.assertEqual(
            no_overdraft_account.reserved_amount,
            Decimal("0.00")
        )

        self.assertEqual(
            no_overdraft_account.available_balance,
            Decimal("500.00")
        )

        self.assertEqual(
            no_overdraft_account.remaining_overdraft,
            Decimal("0.00"),
            msg="Expected remaining overdraft to be 0 when overdraft is not supported"
        )

    def test_has_sufficient_funds_method_when_balance_is_enough(self):
        """Verify a transfer is allowed when the available balance covers the amount."""

        EXPECTED_BALANCE           = Decimal("1000")
        RESERVED_AMOUNT            = Decimal("200")
        EXPECTED_AVAILABLE_BALANCE = EXPECTED_BALANCE - RESERVED_AMOUNT  # £800 available balance

        self.source_current_account.update_reserved_amount(RESERVED_AMOUNT)
        self.source_current_account.save()
        self.source_current_account.refresh_from_db()

        self.assertEqual(self.source_current_account.balance, EXPECTED_BALANCE)
        self.assertEqual(self.source_current_account.available_balance, EXPECTED_AVAILABLE_BALANCE)

        # Assume the user wants to transfer £700, which is within the £800 available balance.
        TRANSFER_AMOUNT = Decimal("700")
        self.assertTrue(TransactionService._has_sufficient_funds(account=self.source_current_account,
                                                                 amount=TRANSFER_AMOUNT,
                                                                 ),
                                                                msg="User should be able to transfer money"
                                                                 )

    def test_has_sufficient_funds_method_when_balance_is_not_enough(self):
        """Verify overdraft capacity is considered when the available balance is insufficient."""

        EXPECTED_BALANCE           = Decimal("1000")
        RESERVED_AMOUNT            = Decimal("1200")
        EXPECTED_AVAILABLE_BALANCE = EXPECTED_BALANCE - RESERVED_AMOUNT  # -200

        self.source_current_account.update_reserved_amount(RESERVED_AMOUNT)
        self.source_current_account.save()

        self.source_current_account.refresh_from_db()

        self.assertEqual(self.source_current_account.balance, EXPECTED_BALANCE)
        self.assertEqual(self.source_current_account.available_balance,
                         EXPECTED_AVAILABLE_BALANCE,
                         msg=f"Available balance the user can use should be {EXPECTED_AVAILABLE_BALANCE}" # -200
                         )


        # £500 overdraft limit - £200 already used = £300 remaining overdraft
        # However the account can't spend £300 because its current available balance is already -£200.
        # Therefore -£200 available + £300 remaining overdraft = £100 which is the spending capacity

        # Assume the user wants to transfer £101 which exceeds spending capacity by 1
        TRANSFER_AMOUNT = Decimal("101")
        self.assertFalse(TransactionService._has_sufficient_funds(account=self.source_current_account,
                                                                 amount=TRANSFER_AMOUNT,
                                                                ),
                                                                 msg="User shouldn't be able to transfer money since it exceeds spending capacity"
                                                                )


        # Test if the user wants to spend the exact spending capacity of £100.
        SPENDING_CAPACITY = Decimal("100")
        self.assertTrue(TransactionService._has_sufficient_funds(account=self.source_current_account,
                                                                 amount=SPENDING_CAPACITY,
                                                                ),
                                                                 msg="User should be able to transfer money"
                                                                )
