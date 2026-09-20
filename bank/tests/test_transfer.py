"""
Tests for internal account-to-account transfers.

The tests cover:
- Successful immediate transfers.
- Transfers placed on hold when the risk threshold is met.
- Account balance changes after completed transfers.
- Reserved funds for pending transfers.
- Ledger entries created for transfers.
- Transfer references shared between related ledger entries.
- Transfer response data and status.
"""


from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.test import TestCase
from django.db.models import Case, Value, When

from authentication.models import User
from bank.management.commands.seed_banks import BANK_SEED_DATA
from bank.models import Bank, BankAccount, LedgerEntry
from bank.services.bank_services import BankProvisioningService
from bank.services.transaction_services import Status, TransactionService, Action
from user_profile.models import UserProfile


from bank.services.funding_service import FundingService
from setup.services.service import AccountOnboardingService


bank_data = BANK_SEED_DATA[0]

RISK_THRESHOLD = settings.RISK_THRESHOLD

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


def get_ledger_by_transfer_reference(transfer_referece: str):
      return LedgerEntry.objects.filter(
                transfer_reference=transfer_referece
                ).alias(

                # Assign custom sort numbers: 1 for DEBIT, 2 for CREDIT
                entry_priority=Case (
                        When(movement=LedgerEntry.Movement.DEBIT, then=Value(1)),
                        When(movement=LedgerEntry.Movement.CREDIT, then=Value(2)),
                        default=Value(3)
                     )
                ).order_by("entry_priority")


class TransferTest(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.username_1 = "username_test_1"
        cls.username_2 = "username_test_2"
        cls.username_3 = "username_test_3"

        cls.user_1  = User.objects.create(username=cls.username_1, email="test_email1@test.com")
        cls.user_2  = User.objects.create(username=cls.username_2, email="test_email2@test.com")

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

    def setUp(self):
        self.funding_amount = Decimal("1000")

        # user 1 will be the source account for her test
        FundingService.add_funds_to_current_account(amount=self.funding_amount, user=self.user_1)

        self.source_current_account  = BankAccount.get_all_account_by_user_profile(
                                                            user_profile=UserProfile.get_profile_by_user(self.user_1)
                                                            )[0]

        self.recipient_current_account =  BankAccount.get_all_account_by_user_profile(
                                                            user_profile=UserProfile.get_profile_by_user(self.user_2)
                                                            )[0]


    def test_accounts_is_created(self):
        EXPECTED_COUNT = 4
        self.assertEqual(BankAccount.objects.count(),
                        EXPECTED_COUNT, "Expected a count of four, i.e 2 current account and 2 saving accounts"
                        )

    def test_if_source_account_is_funded(self):
        EXPECTED_AMOUNT   = Decimal("1000")
        self.assertEqual(self.source_current_account.balance, EXPECTED_AMOUNT, "Expected an amount of 1000")

    def test_transfer_completes_immediately_when_amount_is_below_risk_threshold(self):
        """Verify a valid transfer below the risk threshold completes immediately."""

        transfer_amount     = Decimal("100")
        opening_balance     = Decimal("1000")
        transfer_started_at = timezone.now()

        response = TransactionService.transfer(
            source_account=self.source_current_account,
            recipient_account=self.recipient_current_account,
            amount=transfer_amount,

        )
        transfer_completed_at = timezone.now()

        self.assertIsInstance(response, dict, msg="The returned response should be a dictionary")

        EXPECTED_RESPONSE_KEYS = {
            "SUCCESS",
            "MSG",
            "ACTION",
            "STATUS",
            "AMOUNT",
            "TRANSFER_REFERENCE",
        }

        # test fetch response returned
        self.assertEqual(set(response.keys()), EXPECTED_RESPONSE_KEYS)
        self.assertTrue(response["SUCCESS"])
        self.assertEqual(response["STATUS"], Status.SUCCESS.value)
        self.assertEqual(response["ACTION"], Action.COMPLETED.value)
        self.assertEqual(response["AMOUNT"], transfer_amount)
        self.assertTrue(response["TRANSFER_REFERENCE"])

        # Test the transfer balance
        EXPECTED_SOURCE_ACCOUNT_BALANCE     = 900
        EXPECTED_RECIPIENT_ACCOUNT_BALANCE  = 100

        self.source_current_account.refresh_from_db()
        self.recipient_current_account.refresh_from_db()

        self.assertEqual(self.source_current_account.balance, EXPECTED_SOURCE_ACCOUNT_BALANCE)
        self.assertEqual(self.recipient_current_account.balance, EXPECTED_RECIPIENT_ACCOUNT_BALANCE)

        # test reserved amount
        self.assertEqual(self.source_current_account.reserved_amount, 0)

        # Test Ledger created
        EXPECTED_LEDGER_CREATED = 2

        # returns in the order source account first (debit) and recipient account (credit)
        ledgers = get_ledger_by_transfer_reference(response["TRANSFER_REFERENCE"])

        self.assertEqual(len(ledgers), EXPECTED_LEDGER_CREATED)

        source_account_ledger, recipient_account_ledger = ledgers

        self.assertEqual(source_account_ledger.transfer_reference,
                         recipient_account_ledger.transfer_reference,
                         msg="The transfer reference for both ledger must be the same"

                         )

        # Test if Ledger transfer reference matches the response transfer reference
        self.assertEqual(
            source_account_ledger.transfer_reference,
            response["TRANSFER_REFERENCE"],
            msg="Ledger transfer reference should match the response transfer reference"
        )

        # test the balance recoreded on the ledgers

        # source account ledger -> balances
        self.assertEqual(source_account_ledger.opening_balance, opening_balance) # 1000
        self.assertEqual(source_account_ledger.closing_balance, EXPECTED_SOURCE_ACCOUNT_BALANCE) # 900

        # recipient account ledger -> balances
        self.assertEqual(recipient_account_ledger.opening_balance, 0) # 0
        self.assertEqual(recipient_account_ledger.closing_balance, transfer_amount) # 100

        # test recorded source account ledger types eg transaction type, movement, status
        self.assertEqual(source_account_ledger.transaction_type,
                         LedgerEntry.TransactionType.TRANSFER_OUT,
                         msg="Source account ledger should record money as transfer out"
                         )

        self.assertEqual(source_account_ledger.movement,
                        LedgerEntry.Movement.DEBIT,
                        msg="Source account ledger should record movement as debit"
                        )

        self.assertEqual(source_account_ledger.status,
                        LedgerEntry.Status.COMPLETED,
                        msg="Source account should record status as completed"
                        )


        # test recorded recipient account ledger types eg transaction type, movement, status
        self.assertEqual(recipient_account_ledger.transaction_type,
                         LedgerEntry.TransactionType.TRANSFER_IN,
                         msg="Recipient account ledger should record money as transfer in"
                         )

        self.assertEqual(recipient_account_ledger.movement,
                        LedgerEntry.Movement.CREDIT,
                        msg="Recipient account ledger should record movement as credit"
                        )

        self.assertEqual(recipient_account_ledger.status,
                        LedgerEntry.Status.COMPLETED,
                        msg="Recipient account should record status as completed"
                        )

        # test if completion date is added after a successful transfer
        self.assertGreaterEqual(
            source_account_ledger.completed_on,
            transfer_started_at,
        )
        self.assertLessEqual(
            source_account_ledger.completed_on,
            transfer_completed_at,
        )

    def test_transfer_is_pending_when_amount_meets_risk_threshold(self):

        RISK_THRESHOLD_AMOUNT = Decimal(str(settings.RISK_THRESHOLD))
        SOURCE_BALANCE = RISK_THRESHOLD_AMOUNT

        # Set the source balance to the risk threshold so the transfer
        # passes the sufficient-funds check and reaches the risk review flow.
        self.source_current_account.balance = SOURCE_BALANCE
        self.source_current_account.save()

        source_account_balance_before_transfer   = self.source_current_account.balance
        recipient_account_balance_before_transfer = self.recipient_current_account.balance


        self.assertEqual(self.recipient_current_account.balance, 0)

        response = TransactionService.transfer(
                    source_account=self.source_current_account,
                    recipient_account=self.recipient_current_account,
                    amount=RISK_THRESHOLD_AMOUNT,
                )

        self.assertIsInstance(response, dict, msg="The returned response should be a dictionary")

        EXPECTED_RESPONSE_KEYS = {
                    "SUCCESS",
                    "MSG",
                    "ACTION",
                    "STATUS",
                    "AMOUNT",
                    "TRANSFER_REFERENCE",
                }

        # test fetch response returned are correct
        self.assertEqual(set(response.keys()), EXPECTED_RESPONSE_KEYS)
        self.assertTrue(response["SUCCESS"])
        self.assertEqual(response["STATUS"], Status.PENDING.value)
        self.assertEqual(response["ACTION"], Action.ON_HOLD.value)
        self.assertEqual(response["AMOUNT"], RISK_THRESHOLD_AMOUNT)
        self.assertTrue(response["TRANSFER_REFERENCE"])


        # verify that the source balance isn't changed
        self.source_current_account.refresh_from_db()

        source_account_balance_after_transfer = self.source_current_account.balance

        self.assertEqual(source_account_balance_before_transfer,
                         source_account_balance_after_transfer,
                         msg="Source account balance shouldn't be changed, since transfer is pending"
                         )


        # verify that the recipient account balance isn't changed
        self.recipient_current_account.refresh_from_db()
        recipient_account_balance_after_transfer = self.recipient_current_account.balance

        self.assertEqual(recipient_account_balance_before_transfer,
                         recipient_account_balance_after_transfer,
                         msg="Recipient balance shouldn't be changed, since transfer is pending"
                        )

        # verify that the balance is still 0 which signals that no money was received
        self.assertEqual(self.recipient_current_account.balance, 0, msg="The balance should be 0")

        # verify reserved amount
        self.assertEqual(self.source_current_account.reserved_amount,
                         RISK_THRESHOLD_AMOUNT,
                         msg="Reserved amount for source account should not be empty") # 10000


        # returns in the order source account first (debit) and recipient account (credit)
        ledgers = get_ledger_by_transfer_reference(response["TRANSFER_REFERENCE"])


        EXPECTED_LEDGER_CREATED = 2
        self.assertEqual(len(ledgers), EXPECTED_LEDGER_CREATED)

        source_account_ledger, recipient_account_ledger = ledgers

        # test that the transfer reference share the same reference
        self.assertEqual(source_account_ledger.transfer_reference,
                        recipient_account_ledger.transfer_reference,
                        msg="The transfer reference for both ledger must be the same"

                        )

        # Test if Ledger transfer reference matches the response transfer reference
        self.assertEqual(
                source_account_ledger.transfer_reference,
                response["TRANSFER_REFERENCE"],
            )


        # source account ledger -> balances
        self.assertEqual(source_account_ledger.opening_balance, source_account_balance_before_transfer)
        self.assertEqual(source_account_ledger.closing_balance, source_account_balance_before_transfer)

        # test recorded source account ledger types eg  eg transaction type, movement, status, risk_flag, risk_reaso
        self.assertEqual(source_account_ledger.transaction_type,
                         LedgerEntry.TransactionType.TRANSFER_OUT,
                         msg="Source account ledger should record money as transfer out"
                         )

        self.assertEqual(source_account_ledger.movement,
                        LedgerEntry.Movement.DEBIT,
                        msg="Source account ledger should record movement as debit"
                        )

        self.assertEqual(source_account_ledger.status,
                        LedgerEntry.Status.PENDING,
                        msg="Source account should record status as pending"
                        )

        self.assertEqual(source_account_ledger.source,
                        LedgerEntry.Source.INTERNAL_TRANSFER,
                        msg="Source account transfer should be recorded as internal transfer"
                         )

        self.assertTrue(source_account_ledger.risk_flag, msg="The risk flag should be recorded as true")
        self.assertTrue(source_account_ledger.review_required, msg="The review flag should be recorded as true")
        self.assertIsNotNone(source_account_ledger.risk_reason)

        # recipient ledger entry
        # test recorded recipient ledger types eg transaction type, movement, status, risk_flag, risk_reason
        self.assertEqual(recipient_account_ledger.transaction_type,
                         LedgerEntry.TransactionType.TRANSFER_IN,
                         msg="Recipient account ledger should record money as transfer in"
                         )

        self.assertEqual(recipient_account_ledger.movement,
                        LedgerEntry.Movement.CREDIT,
                        msg="Recipient account ledger should record movement as credit"
                        )

        self.assertEqual(recipient_account_ledger.status,
                        LedgerEntry.Status.PENDING,
                        msg="Recipient account should record status as pending"
                        )

        self.assertEqual(recipient_account_ledger.source,
                        LedgerEntry.Source.INTERNAL_TRANSFER,
                        msg="Recipient account transfer should be recorded as internal transfer"
                         )

        self.assertTrue(recipient_account_ledger.risk_flag, msg="The risk flag should be recorded as true")
        self.assertTrue(recipient_account_ledger.review_required, msg="The review flag should be recorded as true")
        self.assertIsNotNone(recipient_account_ledger.risk_reason)

        # Assert the ledger completed date is none
        self.assertIsNone(source_account_ledger.completed_on)
        self.assertIsNone(recipient_account_ledger.completed_on)
