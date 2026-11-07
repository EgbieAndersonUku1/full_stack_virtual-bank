
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from bank.management.commands.seed_banks import BANK_SEED_DATA
from bank.models import Bank, BankAccount
from bank.services.bank_services import BankProvisioningService
from card.models import BankCard, CardDashboard
from setup.services.service import AccountOnboardingService
from notification.models import Notification

from unittest.mock import patch

from user_profile.models import UserProfile

User = get_user_model()


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


class AccountOnboardingServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="onboarding_test_user",
            email="onboarding_test@example.com",
            password="TestPassword123!"
        )

        bank_data_copy  = BANK_SEED_DATA[0].copy()
        bank_data_copy["offer_saving_account"] = Bank.OfferSavingAccountOptions.NO

        cls.bank = BankProvisioningService.create_bank(
            bank_data_copy,
            source=Bank.Source.SEEDED,
        )

        cls.profile_data = USER_PROFILE_DATA_1.copy()

    @patch("setup.services.service.send_welcome_email_with_async")
    def test_successful_onboarding_creates_account_notification(self, mock_send_email):

        # GIVEN: A user who has not completed onboarding

        # WHEN: The user successfully completes onboarding
        result = AccountOnboardingService.complete_onboarding(
            user=self.user,
            bank=self.bank,
            profile_data=self.profile_data,
            pin="123456",
        )

        # THEN: Onboarding should complete successfully
        self.assertTrue(result)

        # AND: Exactly one account-created notification should exist
        notifications = Notification.objects.filter(
            user=self.user,
            notification_type=Notification.NotificationType.ACCOUNT_CREATED,
        )

        user_profile = UserProfile.get_profile_by_user(self.user)

        self.assertEqual(notifications.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)

        notification = notifications.get()

        # AND: The notification should belong to the correct user
        self.assertEqual(notification.user, self.user)


        self.assertEqual(notification.user.profile, user_profile)
        self.assertEqual(user_profile.user, self.user)

        bank_accounts = BankAccount.get_all_account_by_user_profile(user_profile)
        self.assertEqual(bank_accounts.count(), 1)
        bank_account = bank_accounts.get()

        self.assertEqual(bank_account.user_profile, user_profile)
        self.assertEqual(bank_account.bank, self.bank)

        bank_cards = BankCard.get_by_bank_account(bank_account)

        self.assertEqual(bank_cards.count(), 1)

        bank_card = bank_cards.get()

        self.assertEqual(bank_card.bank_account, bank_account)
        self.assertEqual(bank_card.user, self.user)
        self.assertTrue(bank_card.is_active)

        default_card = BankCard.get_default_card(bank_account)

        self.assertIsNotNone(default_card)
        self.assertEqual(default_card.bank_account, bank_account)
        self.assertTrue(default_card.is_active)


        card_dashboard = CardDashboard.get_by_bank_account(bank_account)

        # self.assertIsNotNone(card_dashboard)
        # self.assertEqual(card_dashboard.bank_account, bank_account)
        # self.assertEqual(card_dashboard.max_cards_to_show, 3)
        # self.assertEqual(card_dashboard.displayed_card_count, 1)

        # AND: The welcome email should have been requested
        mock_send_email.assert_called_once()

