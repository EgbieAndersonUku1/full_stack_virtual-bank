"""
Tests for the recipient verification view.

The tests cover:
- Registration and authentication setup required to access the view.
- Successful recipient verification.
- Recipient verification when no matching account is found.
- Database errors raised while verifying recipient account details.
- Verified recipient details being stored in the session after a successful lookup.
- Ensuring recipient details are not stored in the session when verification fails.
"""



import json

from django.db import DatabaseError
from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch

from authentication.models import Verification
from authentication.models import User
from bank.management.commands.seed_banks import BANK_SEED_DATA
from bank.models import Bank, BankAccount
from bank.services.bank_services import BankProvisioningService
from user_profile.models import UserProfile
from setup.services.service import AccountOnboardingService


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



class VerifyRecipientTest(TestCase):

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

        # create the onboarding
        AccountOnboardingService.complete_onboarding(user=cls.recipient,
                                                     bank=cls.bank,
                                                     profile_data=USER_PROFILE_DATA_2,
                                                     pin="1234"
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
        self.assertTrue(User.objects.filter(username=self.username_1).exists())
        self.assertEqual(response.headers["Location"], "/login/")

        user_verification = Verification.objects.first()
        user              = User.objects.get(username=self.username_1)

        self.assertTrue(user)
        self.assertIsNotNone(user_verification)

        # mark the verification code as used and the email as verified otherwise the system won't allow you in
        user_verification.mark_as_used()
        user.mark_email_as_verified()

        self.client.force_login(user)

        # create onboard for newly registered user
        AccountOnboardingService.complete_onboarding(user=user,
                                                    bank=self.bank,
                                                    profile_data=USER_PROFILE_DATA_1,
                                                    pin="1234"
                                                    )

    def test_if_user_is_registered(self):
        """
        Verify that the test user is successfully registered and has a verified email.

        This confirms the authentication state required by the recipient verification
        view has been established before the view-specific tests are executed.
        """

        user = User.objects.get(username=self.username_1)
        self.assertIsNotNone(user)

        self.assertTrue(Verification.objects.exists())
        self.assertTrue(user.is_user_email_verified())

    def test_verify_recipient_success(self):
        """
        Verify that a valid recipient is successfully identified.

        The test confirms that the view returns a successful verification response
        and stores the verified recipient's sort code and account number in the
        session for use by the subsequent transfer flow.
        """

        recipient_profile = self.recipient_account.user_profile
        response = self.client.post(
            "/dashboard/verify/recipient/",
            data=json.dumps({
                "firstName": recipient_profile.first_name,
                "surname": recipient_profile.last_name,
                "sortCode": self.recipient_account.sort_code.external_sort_code,
                "accountNumber": self.recipient_account.account_number,
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertTrue(response_data)

        data = response_data["data"]

        self.assertTrue(data["SUCCESS"])
        self.assertTrue(data["FOUND"])
        self.assertEqual(data["MSG"], "Account recipient found")
        self.assertEqual(data["ACTION"], "Found")

        # check the session since it stores the recipient account details
        session = self.client.session

        self.assertEqual(
            session["recipient_details"]["sort_code"],
            self.recipient_account.sort_code.external_sort_code,
        )
        self.assertEqual(
            session["recipient_details"]["account_number"],
            self.recipient_account.account_number,
        )

    def test_verify_recipient_when_not_found(self):
        """
        Verify the response returned when no matching recipient is found.

        The test confirms that the lookup is treated as a completed verification
        request with no matching account and that no recipient details are stored
        in the session.
        """
        response = self.client.post(
            "/dashboard/verify/recipient/",
            data=json.dumps({
                "firstName": "first name doesn't exist",
                "surname": "last name doesn't exist",
                "sortCode": "1000000",
                "accountNumber": "10000000",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertTrue(response_data)

        data = response_data["data"]

        self.assertTrue(data["SUCCESS"])
        self.assertFalse(data["FOUND"])
        self.assertEqual(data["MSG"], "Account recipient not found")
        self.assertEqual(data["ACTION"], "Not found")

        # check the session for recipient account details is none
        session = self.client.session

        self.assertIsNone(
            session.get("recipient_details", None),
          )

    @patch("home.views.BankAccount.does_account_exists", side_effect=DatabaseError)
    def test_verify_recipient_database_error(self, mock_does_account_exists):
        """
        Verify the response returned when recipient verification encounters
        a database error.

        The database failure is simulated so the test can confirm that the view
        handles the exception and returns the expected unsuccessful response
        without allowing the database error to propagate to the client.
        """

        recipient_profile = self.recipient_account.user_profile

        response = self.client.post(
        "/dashboard/verify/recipient/",
        data=json.dumps({
            "firstName": recipient_profile.first_name,
            "surname": recipient_profile.last_name,
            "sortCode": self.recipient_account.sort_code.external_sort_code,
            "accountNumber": self.recipient_account.account_number,
        }),
        content_type="application/json",
    )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        data = response_data["data"]

        self.assertFalse(data["SUCCESS"])
        self.assertFalse(data["FOUND"])
        self.assertEqual(data["MSG"], "Unable to verify account recipient")
        self.assertEqual(data["ACTION"], "Error")

        mock_does_account_exists.assert_called_once()
