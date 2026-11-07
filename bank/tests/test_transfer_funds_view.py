


from decimal import Decimal
import json

from django.contrib.auth import get_user_model

from django.test import TestCase
from django.contrib.sessions.backends.base import SessionBase

from unittest.mock import patch

from django.urls import reverse
from requests import request

from authentication.models import Verification
from authentication.models import User
from bank.management.commands.seed_banks import BANK_SEED_DATA
from bank.models import Bank, BankAccount
from bank.services.bank_services import  BankProvisioningService
from user_profile.models import UserProfile
from setup.services.service import AccountOnboardingService
from bank.services.transaction_services import Start, Action, Status
from utils.custom_errors import IncorrectAmountTypeError



User = get_user_model()


USER_PROFILE_DATA_1 = {
    "first_name": "John",
    "last_name": "Smith",
    "city": "London",
    "postcode": "SW1A 1AA",
    "country": "GB",
}

USER_PROFILE_DATA_2 = {
    "first_name": "Jon",
    "last_name": "Smith",
    "city": "London",
    "postcode": "SW1A 1AA",
    "country": "GB",
}

payload = {
         "bankTransferSelection": "bank",
            "amount": "100.00",
            "transferStart": Start.IMMEDIATELY.value,
            "pin": "123456",
        }

URL = reverse("transfer_funds")


def simulate_successful_verified_client(session: SessionBase, sort_code: str, account_number: str):
    # Simulate a successfully verified recipient from the previous view flow.
    client_session = session
    client_session["recipient_details"] = {
                "sort_code": sort_code,
                "account_number": account_number,
            }
    client_session.save()


class TransferFundsTest(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.username_1       = "test_user"
        cls.username_1_email = "test_user@example.com"

        # recipient
        cls.recipient_username  = "test_recipient"
        cls.recipient_email     = "test_recipient_emai@hotmail.com"

        cls.recipient = User.objects.create(username=cls.recipient_email, email=cls.recipient_email)

        cls.bank = BankProvisioningService.create_bank(
            BANK_SEED_DATA[0].copy(),
            source=Bank.Source.SEEDED,
        )

        # create the onboarding for the recipient
        AccountOnboardingService.complete_onboarding(user=cls.recipient,
                                                     bank=cls.bank,
                                                     profile_data=USER_PROFILE_DATA_2,
                                                     pin="123456"
                                                    )

        cls.recipient_account =  BankAccount.get_all_account_by_user_profile(
                                            user_profile=UserProfile.get_profile_by_user(cls.recipient)
                                           )[0]


    def setUp(self):

        # replaces the actual email with a patch to prevent it from sending emails
        self.email_patcher   = patch("authentication.views.send_confirmation_email_with_async")
        self.mock_send_email = self.email_patcher.start()
        self.addCleanup(self.email_patcher.stop)

        # register the user
        response = self.client.post(
            "/register/",
            data={
                "username": self.username_1,
                "email": self.username_1_email,
                "password": "12345678Aa!",
                "confirm_password": "12345678Aa!",
                "terms_and_condition": "on",
            },
        )

        self.assertEqual(response.status_code, 302)

        user              = User.objects.get(username=self.username_1)
        user_verification = Verification.objects.get(user=user)

        # mark the verification code as used and the email as verified otherwise the system won't allow you in
        user_verification.mark_as_used()
        user.mark_email_as_verified()

        self.client.force_login(user)

        # create onboard for newly registered user
        AccountOnboardingService.complete_onboarding(user=user,
                                                    bank=self.bank,
                                                    profile_data=USER_PROFILE_DATA_1,
                                                    pin="123456"
                                                    )
        self.source_account = BankAccount.get_all_account_by_user_profile(
                                user_profile=UserProfile.get_profile_by_user(user)
                                )[0]

        self.FUND_ACCOUNT_AMOUNT    = Decimal("1000")
        self.source_account.balance = self.FUND_ACCOUNT_AMOUNT
        self.source_account.save()

    @patch("home.views.BankAccountCacheService.get_total_account_balance")
    @patch("home.views.TransactionService.process_transfer")
    def test_transfer_funds_success(self, mock_process_transfer, mock_get_total_balance):
        """
        Verify that a valid immediate transfer request is processed successfully.

        The test confirms that the transfer view correctly converts the incoming
        request data, calls the transaction service with the expected values,
        returns the successful transfer response and updated balance, and removes
        the verified recipient details from the session.
        """

        mock_process_transfer.return_value = {
            "SUCCESS": True,
            "MSG": "Transfer completed successfully",
            "ACTION": Action.COMPLETED.value,
            "STATUS": Status.SUCCESS.value,
            "AMOUNT": Decimal("100"),
            "TRANSFER_REFERENCE": "test-transfer-reference",
        }

        mock_get_total_balance.return_value = Decimal("900")

        TRANSFER_AMOUNT = Decimal("100")

        simulate_successful_verified_client(
            session=self.client.session,
            sort_code=self.recipient_account.sort_code.external_sort_code,
            account_number=self.recipient_account.account_number
        )

        response = self.client.post(URL, data=json.dumps({
            "bankTransferSelection": "bank",
            "amount": str(TRANSFER_AMOUNT),
            "transferStart": Start.IMMEDIATELY.value,
            "pin" : "123456",
        }),
         content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        data = response_data["data"]

        # verify the response
        self.assertTrue(data["SUCCESS"])
        self.assertEqual(data["MSG"], "Transfer completed successfully",)
        self.assertEqual(data["ACTION"], Action.COMPLETED.value)
        self.assertEqual(data["STATUS"], Status.SUCCESS.value)
        self.assertEqual(data["AMOUNT"], str(TRANSFER_AMOUNT))
        self.assertEqual(data["TRANSFER_REFERENCE"], "test-transfer-reference")


        self.assertEqual(Decimal(data["BALANCE"]), self.FUND_ACCOUNT_AMOUNT - TRANSFER_AMOUNT)

        mock_get_total_balance.assert_called_once_with(self.source_account.user_profile.user)


        self.assertIsNone(self.client.session.get("recipient_details"))

        mock_process_transfer.assert_called_once_with(
            pin="123456",
            recipient_account=self.recipient_account,
            source_account=self.source_account,
            amount=TRANSFER_AMOUNT,
            start=Start.IMMEDIATELY,
        )

    @patch("home.views.TransactionService.process_transfer")
    def test_missing_required_keys(self, mock_process_transfer):
        """
        Verify that the transfer view rejects requests missing required fields.

        Each required transfer field is removed individually to confirm that the
        view returns an unsuccessful response without calling the transaction
        service.
        """
        payload = {
            "bankTransferSelection": "bank",
            "amount": "100.00",
            "transferStart": Start.IMMEDIATELY.value,
            "pin": "123456",
        }

        for missing_key in payload:
            with self.subTest(missing_key=missing_key):
                request_data = payload.copy()
                request_data.pop(missing_key)

                response = self.client.post(
                    reverse("transfer_funds"),
                    data=json.dumps(request_data),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 200)

                data = response.json()["data"]

                self.assertFalse(data["SUCCESS"])
                self.assertEqual(data["ACTION"], "Missing key")
                self.assertEqual(data["STATUS"], Status.UNSUCCESSFUL.value)
                self.assertIn(missing_key, data["MSG"])
                self.assertEqual(data["AMOUNT"], "0.00")
                self.assertEqual(data["TRANSFER_REFERENCE"], "")
                self.assertEqual(data["BALANCE"], "1000.00")

        mock_process_transfer.assert_not_called()

    @patch("home.views.TransactionService.process_transfer")
    def test_missing_session(self, mock_process_transfer):
        """
        Verify that the view returns the appropriate response when no
        verified recipient details are present in the session.
        """

        response = self.client.post(
            reverse("transfer_funds"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertFalse(data["SUCCESS"])
        self.assertEqual(data["ACTION"], "Recipient not found")
        self.assertEqual(data["STATUS"], Status.UNSUCCESSFUL.value)
        self.assertEqual(
            data["MSG"],
            "Recipient account details could not be found",
        )
        self.assertEqual(data["AMOUNT"], "0.00")
        self.assertEqual(data["TRANSFER_REFERENCE"], "")
        self.assertEqual(data["BALANCE"], "1000.00")

        mock_process_transfer.assert_not_called()

    @patch("home.views.TransactionService.process_transfer")
    def test_transfer_funds_when_recipient_account_not_found(self, mock_process_transfer):
        """
        Verify that the transfer view returns an unsuccessful response when
        the recipient account cannot be identified.
        """

        simulate_successful_verified_client(
            session=self.client.session,
            sort_code="missing account",
            account_number="missing account number"
        )

        response = self.client.post(
                           URL,
                            data=json.dumps(payload),
                            content_type="application/json",
                        )


        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertFalse(data["SUCCESS"])
        self.assertEqual(data["MSG"], "Unable to identify the transfer accounts")
        self.assertEqual(data["ACTION"], "Account not found")
        self.assertEqual(data["STATUS"], Status.UNSUCCESSFUL.value)

        self.assertEqual(data["AMOUNT"], "0.00")
        self.assertEqual(data["TRANSFER_REFERENCE"], "")
        self.assertEqual(data["BALANCE"], "1000.00")

        mock_process_transfer.assert_not_called()

    @patch("home.transfer.utils.BankAccountCacheService.get_total_account_balance", return_value=Decimal("1000.00"))
    @patch("home.views.BankAccountCacheService.get_current_account", return_value=None)
    @patch("home.views.TransactionService.process_transfer")
    def test_transfer_funds_when_source_account_not_found(self, mock_process_transfer,
                                                   mock_get_current_account,
                                                   mock_get_total_balance,
                                                   ):
        """
        Verify that the transfer view returns an unsuccessful response when
        the source account cannot be identified.
        """

        simulate_successful_verified_client(
             session=self.client.session,
             sort_code=self.recipient_account.sort_code.external_sort_code,
             account_number=self.recipient_account.account_number,
        )

        response = self.client.post(
                           URL,
                            data=json.dumps(payload),
                            content_type="application/json",
                        )


        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertFalse(data["SUCCESS"])
        self.assertEqual(data["MSG"], "Unable to identify the transfer accounts")
        self.assertEqual(data["ACTION"], "Account not found")
        self.assertEqual(data["STATUS"], Status.UNSUCCESSFUL.value)

        self.assertEqual(data["AMOUNT"], "0.00")
        self.assertEqual(data["TRANSFER_REFERENCE"], "")
        self.assertEqual(data["BALANCE"], "1000.00")

        mock_process_transfer.assert_not_called()
        mock_get_current_account.assert_called_once_with(
                     user=self.source_account.user_profile.user
       )

    @patch("home.views.TransactionService.process_transfer")
    def test_transfer_funds_when_transfer_type_not_supported(self, mock_process_transfer):
        """
        Verify that the transfer view rejects unsupported transfer types
        without calling the transaction service.
        """
        simulate_successful_verified_client(
            session=self.client.session,
            sort_code=self.recipient_account.sort_code.external_sort_code,
            account_number=self.recipient_account.account_number
            )

        response = self.client.post(URL, data=json.dumps({
            "bankTransferSelection": "something not on the list",
            "amount": "100.0",
            "transferStart": Start.IMMEDIATELY.value,
            "pin" : "123456",
            }),
             content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]

        self.assertFalse(data["SUCCESS"])
        self.assertEqual(data["MSG"], "The selected transfer type is not supported")
        self.assertEqual(data["ACTION"], "Invalid transfer type")
        self.assertEqual(data["STATUS"], Status.UNSUCCESSFUL.value)

        self.assertEqual(data["AMOUNT"], "0.00")
        self.assertEqual(data["TRANSFER_REFERENCE"], "")
        self.assertEqual(data["BALANCE"], "1000.00")

        mock_process_transfer.assert_not_called()

    @patch("home.views.TransactionService.process_transfer")
    def test_transfer_funds_when_amount_is_invalid(self, mock_process_transfer):
        """
        Verify that the transfer view returns an unsuccessful response when
        the transaction service raises an invalid amount error.
        """
        simulate_successful_verified_client(
                session=self.client.session,
                sort_code=self.recipient_account.sort_code.external_sort_code,
                account_number=self.recipient_account.account_number
                )

        mock_process_transfer.side_effect = IncorrectAmountTypeError

        amounts_to_test = ["0", "-1"]

        for amount in amounts_to_test:
            with self.subTest(amount=amount):
                response = self.client.post(URL, data=json.dumps({
                        "bankTransferSelection": "bank",
                        "amount": amount,
                        "transferStart": Start.IMMEDIATELY.value,
                        "pin" : "123456",
                        }),
                        content_type="application/json",
                        )

                self.assertEqual(response.status_code, 200)

                data = response.json()["data"]

                self.assertFalse(data["SUCCESS"])
                self.assertEqual(data["MSG"], "The transfer amount is invalid")
                self.assertEqual(data["ACTION"], "Invalid amount")
                self.assertEqual(data["STATUS"], Status.UNSUCCESSFUL.value)

                self.assertEqual(data["AMOUNT"], "0.00")
                self.assertEqual(data["TRANSFER_REFERENCE"], "")
                self.assertEqual(data["BALANCE"], "1000.00")

        self.assertEqual(mock_process_transfer.call_count, 2)

        calls = mock_process_transfer.call_args_list

        self.assertEqual(calls[0].kwargs["amount"], Decimal("0"))
        self.assertEqual(calls[1].kwargs["amount"], Decimal("-1"))

