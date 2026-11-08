
from decimal import Decimal

from django.utils import timezone
from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from unittest.mock import patch

from bank.models import Bank, BankAccount
from bank.services.bank_services import AccountService, BankProvisioningService
from bank.management.commands.seed_banks import BANK_SEED_DATA

from card.models import BankCard, CardDashboard
from setup.services.service import AccountOnboardingService
from notification.models import Notification
from utils.custom_errors import SavingAccountNotOfferedError


bank_1 =  {

    "name": "Atlas Aurora National Bank",
    "country": "GB",
    "description": "A modern digital-first bank focusing on personal banking and flexible savings solutions.",
    "logo": "banks/logo/atlas-bank.png",
    "branch_name": "London Central Branch",
    "address_line_1": "12 King Street",
    "address_line_2": "Westminster",
    "post_code": "SW1A 1AA",
    "interest_period": "MONTHLY",
    "interest_rate": Decimal("0.07"),
    "phone_number": "+44 20 7946 0123",
    "minimum_opening_deposit": Decimal("0.00"),
    "offer_overdraft": "Yes",
    "offer_loans": "No",
    "offer_saving_account": "Yes",
    "monthly_deposit": Decimal("0.00"),
    }


class TestBankOpeningService(TestCase):

    def _get_bank_payload(self, **overrides):
        """Helper factory to generate default bank data with optional overrides."""
        default_payload = {
            "name": "National Bank",
            "country": "GB",
            "description": "A modern digital-first bank focusing on personal banking and flexible savings solutions.",
            "logo": "banks/logo/atlas-bank.png",
            "branch_name": "London Central Branch",
            "address_line_1": "12 King Street",
            "address_line_2": "Westminster",
            "post_code": "SW1A 1AA",
            "interest_period": "MONTHLY",
            "interest_rate": Decimal("0.07"),
            "phone_number": "+44 20 1946 0123",
            "minimum_opening_deposit": Decimal("0.00"),
            "offer_overdraft": "Yes",
            "offer_loans": "No",
            "offer_saving_account": "Yes",  # Default baseline
            "monthly_deposit": Decimal("0.00"),
        }
        default_payload.update(overrides)
        return default_payload

    def test_create_bank_item_excludes_savings_account_when_not_offered(self):

        # Override the default payload
        bank_data = self._get_bank_payload(offer_saving_account="No")

        BankProvisioningService.create_bank(bank_data, Bank.Source.SEEDED)

        savings_exist = Bank.objects.filter(offer_saving_account=Bank.OfferSavingAccountOptions.YES).exists()
        self.assertFalse(savings_exist, "Savings account should not exist upon bank creation.")

    def test_open_bank_account_raises_error_if_savings_not_offered(self):

        bank_data = self._get_bank_payload(offer_saving_account="No")
        bank = BankProvisioningService.create_bank(bank_data, Bank.Source.SEEDED)

        with self.assertRaises(SavingAccountNotOfferedError) as custom:
            AccountService.open_bank_account(bank=bank, account_type=BankAccount.AccountType.SAVINGS) # Create an account with saving for a bank that doesn't offer it

        self.assertEqual(str(custom.exception), "Saving account is not offerred with this bank")

    def test_default_bank_offers_overdraft(self):

        bank_data = self._get_bank_payload()
        bank = BankProvisioningService.create_bank(bank_data, Bank.Source.SEEDED)

        overdraft_exists = Bank.objects.filter(offer_overdraft=Bank.OverDraftOptions.YES).exists()
        self.assertTrue(overdraft_exists, "This bank should have an overdraft facility.")

        # Ensure that opening an account at a bank offering overdraft enables overdraft support on the account
        account = AccountService.open_bank_account(bank=bank)
        account.refresh_from_db()

        self.assertTrue(account.supports_overdraft, "Account should support overdraft when the bank offers it.")

    def test_default_bank_excludes_overdraft(self):

        bank_data = self._get_bank_payload(offer_overdraft=Bank.OverDraftOptions.NO)
        bank = BankProvisioningService.create_bank(bank_data, Bank.Source.SEEDED)

        overdraft_exists = Bank.objects.filter(offer_overdraft=Bank.OverDraftOptions.NO).exists()
        self.assertTrue(overdraft_exists, "This bank should not have an overdraft facility.")

        # Ensure that opening an account at a bank not offering overdraft does not enable overdraft support on the account
        account = AccountService.open_bank_account(bank=bank)
        account.refresh_from_db()

        self.assertFalse(account.supports_overdraft, "Account should not support overdraft when the bank doesn't offers it.")

    def test_default_bank_does_not_offer_loan(self):

        bank_data = self._get_bank_payload()
        bank = BankProvisioningService.create_bank(bank_data, Bank.Source.SEEDED)

        loan_exists = Bank.objects.filter(offer_loans=Bank.OfferLoans.NO).exists()
        self.assertTrue(loan_exists, "This bank should not have an loan facilities.")

        # Ensure that opening an account at a bank not offering loan does not enable loan support on the account
        account = AccountService.open_bank_account(bank=bank)
        account.refresh_from_db()

        self.assertFalse(account.supports_loans, "Account should not support loans when the bank doesn't offer it")




class BankCreationTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.bank_1 = bank_1
        cls.bank = BankProvisioningService.create_bank(cls.bank_1.copy(), Bank.Source.SEEDED)

    def test_banks_are_created(self):
        self.assertEqual(Bank.objects.count(), 1)

    def test_bank_attribrutes_are_correct(self):
        self.bank.refresh_from_db()

        self.assertTrue(self.bank.id)
        self.assertEqual(self.bank_1["name"], self.bank.name)
        self.assertEqual(self.bank_1["country"], self.bank.country)
        self.assertEqual(self.bank_1["description"], self.bank.description)
        self.assertEqual(self.bank_1["logo"], self.bank.logo)
        self.assertEqual(self.bank_1["branch_name"], self.bank.branch_name)
        self.assertEqual(self.bank_1["address_line_1"], self.bank.address_line_1)
        self.assertEqual(self.bank_1["address_line_2"], self.bank.address_line_2)
        self.assertEqual(self.bank_1["post_code"], self.bank.post_code)
        self.assertEqual(self.bank_1["interest_period"], self.bank.InterestPeriod.MONTHLY)
        self.assertEqual(self.bank_1["phone_number"], self.bank.phone_number)
        self.assertEqual(self.bank_1["minimum_opening_deposit"], self.bank.minimum_opening_deposit)
        self.assertEqual(self.bank_1["offer_overdraft"], self.bank.offer_overdraft)
        self.assertEqual(self.bank_1["offer_loans"], self.bank.offer_loans)
        self.assertEqual(self.bank_1["offer_saving_account"], self.bank.offer_saving_account)
        self.assertEqual(self.bank_1["monthly_deposit"], self.bank.monthly_deposit)

        now = timezone.now().replace(microsecond=0, minute=0, second=0)
        self.assertIsNotNone(self.bank.created_on)
        self.assertGreaterEqual(self.bank.created_on.replace(microsecond=0, minute=0, second=0), now)

    def test_cannot_create_bank_with_duplicate_name(self):
        """Ensure a new bank cannot be registered if its name is already taken."""

        with self.assertRaises(IntegrityError):
            BankProvisioningService.create_bank(self.bank_1, Bank.Source.SEEDED)



class BankCreationMethodTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.bank_1 = bank_1
        cls.bank = BankProvisioningService.create_bank(cls.bank_1.copy(), Bank.Source.SEEDED)

    def test_creation_count(self):
        self.assertEqual(Bank.objects.count(), 1)


    def test_logo_image_method(self):
        self.assertTrue(self.bank.logo_image)

    def test_interest_rate_percent_property(self):

        value = self.bank.interest_rate_bps
        self.assertIsInstance(value, (int, float))

    def test_bank_count_property_has_no_bank_accounts_when_bank_is_created(self):
        self.assertEqual(self.bank.bank_accounts_count, 0)

    def test_bank_count_property_has_bank_accounts_when_accounts_are_added_to_it(self):

        # Added a couple of accounts to the newly created bank. Add 4  basic accounts and 4 saving accounts

        for _ in range(4):
            AccountService.open_bank_account(bank=self.bank)
            AccountService.open_bank_account(bank=self.bank, account_type=BankAccount.AccountType.SAVINGS)

        EXPECTED_COUNT = 8
        count          = self.bank.bank_accounts_count

        self.assertEqual(count, EXPECTED_COUNT)

        # test that the actual account types were created
        self.assertEqual(BankAccount.objects.filter(account_type=BankAccount.AccountType.BASIC).count(), 4)
        self.assertEqual(BankAccount.objects.filter(account_type=BankAccount.AccountType.SAVINGS).count(), 4)

    def test_full_address_property_returns_full_address(self):

        # manually create the address
        country_name = {"GB": "United Kingdom"}
        address_parts = []
        address_parts.append(self.bank_1["address_line_1"],)
        address_parts.append(self.bank_1["address_line_2"])
        address_parts.append(self.bank_1["post_code"],)
        address_parts.append(country_name[self.bank_1["country"]]) # map country code to country name

        full_address = ", ".join(address_parts)

        # compare with the actually address
        self.assertEqual(self.bank.full_address, full_address, "Address should match the expected address")

    def test_get_by_bank_id_method(self):

        bank_id = self.bank.id
        bank    = Bank.get_by_id(bank_id)

        self.assertIsNotNone(bank, "Bank instance should not be None")
        self.assertIsInstance(bank, Bank, "bank instance should be an instance of Bank")

    def test_get_by_bank_name_method(self):

        name = self.bank.name
        bank = Bank.get_by_bank_name(name)

        self.assertIsNotNone(bank, "Bank instance should not be None")
        self.assertIsInstance(bank, Bank, "bank instance should be an instance of Bank")

    def test_get_all_banks_method(self):

        EXPECTED_COUNT = 9

        for bank_data in BANK_SEED_DATA:
            try:
                BankProvisioningService.create_bank(bank_data.copy(), source=Bank.Source.SEEDED)
            except IntegrityError:
                pass

        banks = Bank.get_all_banks()
        self.assertEqual(banks.count(), EXPECTED_COUNT)













