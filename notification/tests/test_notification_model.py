import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from unittest.mock import patch
from notification.models import Notification
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone
from django.db import IntegrityError, transaction

from notification.models import Notification
from notification.services.notification_service import NotificationService, NOTIFICATION_SUMMARY_CACHE_TTL


User = get_user_model()

IS_READ    = True
IS_UNREAD  = False


test_cases = [
            (
                Notification.NotificationType.ACCOUNT_CREATED,
                Notification.NotificationTitle.ACCOUNT_CREATED,
                Notification.NotificationMessage.ACCOUNT_CREATED,
                IS_READ

            ),
            (
                Notification.NotificationType.TRANSFER_SENT,
                Notification.NotificationTitle.TRANSFER_SENT,
                Notification.NotificationMessage.TRANSFER_SENT,
                IS_UNREAD

            ),
            (
                Notification.NotificationType.TRANSFER_RECEIVED,
                Notification.NotificationTitle.TRANSFER_RECEIVED,
                Notification.NotificationMessage.TRANSFER_RECEIVED,
                IS_UNREAD
            ),
            (
                Notification.NotificationType.CARD_REQUEST_APPROVED,
                Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                IS_READ

            ),
            (
                Notification.NotificationType.CARD_REQUEST_REJECTED,
                Notification.NotificationTitle.CARD_REQUEST_REJECTED,
                Notification.NotificationMessage.CARD_REQUEST_REJECTED,
                IS_READ
            ),
]


def create_user(username="test_user", email="test_email"):
    return User.objects.create(
        username=username,
        email=email
    )

def create_user_notifications(user, cases: list | None = None):
    """
    Create a collection of notifications for the specified user.

    Uses the supplied test cases to determine each notification's type,
    title, message and read status.
    """
    if cases is None:
        cases = test_cases

    for notif_type, expected_title, expected_message, is_read in cases:
        Notification.objects.create(
            user=user,
            notification_type=notif_type,
            title=expected_title.label,
            message=expected_message.label,
            is_read=is_read,
        )

class NotificationModelTest(TestCase):
    """
    Test notification model creation and database-level constraints.
    """

    def test_notification_creation_for_all_types(self):
        """
        Verify that notifications of every supported type can be created
        with the expected title and message.

        Also verifies that newly created notifications use the default
        unread state, have no read timestamp, receive a unique UUID,
        and are associated with the correct user.
        """
        user = create_user()
        for notif_type, expected_title, expected_message, _ in test_cases:

            with self.subTest(notification_type=notif_type):

                Notification.objects.all().delete()

                 # Assert that the times created and updated are created
                before_creation = timezone.now()

                notification = Notification.objects.create(
                    user=user,
                    notification_type=notif_type,
                    title=expected_title.label,
                    message=expected_message.label,
                )

                after_creation = timezone.now()


                self.assertEqual(Notification.objects.count(), 1, "The number of notifications created should be 1")

                notification.refresh_from_db()

                # Assert UUID fields
                self.assertTrue(notification.notification_id)
                self.assertIsInstance(notification.notification_id, uuid.UUID, "Id must be an instance of UUID")

                # The assertions will now perfectly match
                self.assertEqual(notification.title, expected_title.label, "Title doesn't match expected title")
                self.assertEqual(notification.message, expected_message.label, "Expected message does not match")

                # Assert flags and times
                self.assertFalse(notification.is_read, "The is_read should be created as false")

                # Assert that the read_at message time is blank, since a newly created notification object shouldn't have a time
                self.assertIsNone(notification.read_at)


                self.assertLessEqual(before_creation, notification.created_at)
                self.assertLessEqual(notification.created_at, after_creation)
                self.assertLessEqual(before_creation, notification.updated_at)
                self.assertLessEqual(notification.updated_at, after_creation)

                self.assertIsInstance(notification.user, User, "The notification model is not a User object")


                self.assertEqual(notification.user, user)

    def test_notification_id_must_be_unique(self):
        """
        Verify that notification IDs must be unique across all notification records.

        Attempts to create two notifications using the same UUID but belonging
        to different users. The database should reject the second record by
        raising an IntegrityError.
        """
        NOTIFICATION_ID =  str(uuid.uuid4()) # e.g., '7c9e6679-7425-40de-944b-e07fc1f90ae7'

        user_1 = create_user(username="first_username", email="first_user@example.com")
        user_2 = create_user(username="second_username", email="second_user@example.com")


        # Create a notification with id to override the default created notification id
        Notification.objects.create(
                        notification_id=NOTIFICATION_ID,
                        user=user_1,
                        notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                        title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                        message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                    )

        # Create a second user with the same notification id and see if a unique integration error is raise

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Notification.objects.create(
                                    notification_id=NOTIFICATION_ID,
                                    user=user_2,
                                    notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                                    title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                                    message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                                )


class NotificationModelMethodTest(TestCase):

    def setUp(self) -> None:
        """
        Sets up a user and timestamp
        """
        self.user = create_user()
        self.time = timezone.now().replace(microsecond=0)

    def test_get_read_notifications_method(self):
        """
        Verify that get_read_notifications() returns the user's read notifications.

        Checks that the returned value is a QuerySet containing the expected
        number of notifications and that the retrieved notification has the
        correct read status and read timestamp.
        """

        EXPECTED_COUNT = 1

        # create a read notification
        Notification.objects.create(
                                user=self.user,
                                notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                                title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                                message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                                is_read=True,
                                read_at=self.time
                            )

        # test the read method returns a read notification
        notifications = Notification.get_read_notifications(self.user)

        self.assertIsNotNone(notifications, "Notification for read shouldn't be None")
        self.assertIsInstance(notifications, QuerySet)
        self.assertEqual(notifications.count(), EXPECTED_COUNT)


        notification = notifications.first()

        # test correct parameters are returned
        self.assertTrue(notification.is_read, "is_read parameter should be true")
        self.assertEqual(notification.read_at, self.time)

    def test_get_unread_notifications_excludes_read(self):
        """
        Verify that get_unread_notifications() excludes read notifications.

        Creates a read notification and retrieves the user's unread
        notifications. The returned QuerySet should be empty because
        read notifications must not be included when requesting
        unread notifications.
        """
        # Create a read notification
        Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
            title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
            message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
            is_read=True,
            read_at=self.time
        )

        notifications = Notification.get_unread_notifications(self.user)
        self.assertEqual(notifications.count(), 0, "Unread notifications should not be returned.")

    def test_get_read_notifications_only_returns_current_users_notifications(self):
        """Ensure User A cannot see User B's read notifications."""

        other_user = create_user(username="other_username", email="other_user_email@example.com")

        # Create read notification for User B
        Notification.objects.create(
             user=other_user,
             notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
             title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
             message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
             is_read=True,
             read_at=self.time
        )

        user_a_notifications = Notification.get_read_notifications(self.user)
        self.assertEqual(user_a_notifications.count(), 0, "User should not see other users' notifications.")

    def test_get_unread_notifications_method(self):
        """
        Verify that get_unread_notifications() returns the user's unread
        notifications.

        Checks that the returned value is a QuerySet containing the expected
        number of notifications and that the retrieved notification is
        marked as unread with no read timestamp.
        """
        EXPECTED_COUNT = 1

        # create an unread notification
        Notification.objects.create(
                                    user=self.user,
                                    notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                                    title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                                    message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                                    )

        # Verify the unread method returns an unread notification.
        notifications = Notification.get_unread_notifications(self.user)

        self.assertIsNotNone(notifications, "Notification for unread shouldn't be None")
        self.assertIsInstance(notifications, QuerySet)
        self.assertEqual(notifications.count(), EXPECTED_COUNT)

        notification = notifications.first()

        # test correct parameters are returned
        self.assertFalse(notification.is_read, "Notification should be unread")
        self.assertIsNone(notification.read_at)

    def test_get_read_notifications_excludes_unread(self):
        """
        Verify that get_read_notifications() excludes unread notifications.

        Creates an unread notification and retrieves the user's read notifications.
        The returned queryset should be empty because unread notifications must
        not be included when requesting read notifications.
        """
        # Create an unread notification
        Notification.objects.create(
                user=self.user,
                notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
            )

        notifications = Notification.get_read_notifications(self.user)
        self.assertEqual(notifications.count(), 0, "read notifications should not be returned.")


    def test_get_notification_by_id_method(self):
        """
        Verify that a notification can be retrieved using its unique ID.

        Creates a notification with a known UUID and retrieves it using
        the notification ID and associated user. Confirms that the
        retrieved notification has the expected UUID.
        """

        NOTIFICATION_ID =  str(uuid.uuid4()) # e.g., '7c9e6679-7425-40de-944b-e07fc1f90ae7'

        # Create a notification with id to override the default created when notification id is None
        Notification.objects.create(
                        notification_id=NOTIFICATION_ID,
                        user=self.user,
                        notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                        title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                        message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                    )

        notification = Notification.get_notification_by_id(NOTIFICATION_ID, self.user)

        self.assertIsNotNone(notification, "Notification id should not be none")

        self.assertEqual(str(notification.notification_id), NOTIFICATION_ID, "Notification id should match")

    def test_get_unread_notification_count_method(self):
        """
        Verify that get_unread_notification_count() returns the correct
        number of unread notifications belonging to the user.

        Also checks that the returned count is an integer and matches
        the expected number of unread notifications.
        """
        Notification.objects.create(
                                user=self.user,
                                notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                                title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                                message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                            )

        EXPECTED_COUNT = 1
        received_count = Notification.get_unread_notification_count(self.user)

        self.assertIsNotNone(received_count, "Received count should not be None")
        self.assertIsInstance(received_count, int, "Received count should be an integer")
        self.assertEqual(EXPECTED_COUNT, received_count)

    def test_get_read_notification_count_method(self):
        """
        Verify that get_read_notification_count() returns the correct
        number of read notifications belonging to the user.

        Also checks that the returned count is an integer and matches
        the expected number of read notifications.
        """
        Notification.objects.create(
                                user=self.user,
                                notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                                title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                                message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                                is_read=True,
                                read_at=self.time
                            )

        EXPECTED_COUNT = 1
        received_count = Notification.get_read_notification_count(self.user)

        self.assertIsNotNone(received_count, "Received count should not be None")
        self.assertIsInstance(received_count, int, "Received count should be an integer")
        self.assertEqual(EXPECTED_COUNT, received_count)

    def test_get_notifications_by_user_method(self):
        """
        Verify that get_notifications_by_user() retrieves all notifications
        belonging to the specified user, regardless of their read status.

        Checks that the returned collection contains the expected number
        of notification records.
        """
        # create a few notifications belonging to the user
        create_user_notifications(self.user)

        EXPECTED_NOTIFICATIONS_CREATED = len(test_cases)

        received_notifications = Notification.get_notifications_by_user(self.user)
        self.assertIsNotNone(received_notifications)

        self.assertEqual(received_notifications.count(), EXPECTED_NOTIFICATIONS_CREATED)

    def test_get_notification_stats_method(self):
        """
        Verify that get_notification_stats() returns the correct notification
        statistics for the specified user.

        Checks that the returned dictionary contains the expected keys,
        that all statistic values are integers, and that the aggregated
        read, unread, total and today's notification counts match
        the expected results.
        """
        create_user_notifications(self.user)

        EXPECTED_KEY_LENGTH = 4 # read, unread, today and total
        notification_stats = Notification.get_notification_stats(self.user)

        self.assertIsInstance(notification_stats, dict)

        self.assertEqual(len(notification_stats.keys()), EXPECTED_KEY_LENGTH)

        # check if notification_stats contains the expected keys
        self.assertIn("read", notification_stats, "read should be in the notification stats")
        self.assertIn("unread", notification_stats, "unread should be in the notification stats")
        self.assertIn("today", notification_stats, "today should be in the notification stats")
        self.assertIn("total", notification_stats, "total should be in the notification stats")

        # check that their values are stored as integers
        for value in notification_stats.values():
            self.assertIsInstance(value, int, f"{value} is not an integer")

        # checked if the values stored match expected results
        EXPECTED_READ_NOTIFICATIONS_COUNT   = 3
        EXPECTED_UNREAD_NOTIFICATION_COUNT  = 2
        EXPECTED_TOTAL_NOTIFICATIONS_COUNT  = 5
        EXPECTED_TODAY_NOTIFICATIONS_COUNT  = 5

        self.assertEqual(notification_stats["read"],   EXPECTED_READ_NOTIFICATIONS_COUNT)
        self.assertEqual(notification_stats["unread"], EXPECTED_UNREAD_NOTIFICATION_COUNT)
        self.assertEqual(notification_stats["today"],  EXPECTED_TODAY_NOTIFICATIONS_COUNT)
        self.assertEqual(notification_stats["total"],  EXPECTED_TOTAL_NOTIFICATIONS_COUNT)

    def test_get_notification_by_id_does_not_return_another_users_notification(self):
        """
        Verify that a user cannot retrieve another user's notification
        even when they know its notification ID.
        """

        user_1 = create_user(username="first_username", email="first_user@example.com")
        user_2 = create_user(username="second_username", email="second_user@example.com")
        EXPECTED_NOTIFICATION_COUNT = 2

        for user in [user_1, user_2]:
            Notification.objects.create(
                                    user=user,
                                    notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                                    title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                                    message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                                )

        self.assertEqual(Notification.objects.count(),
                         EXPECTED_NOTIFICATION_COUNT,
                         msg="There should be two newly created account"
                         )

        user_1_notification = Notification.objects.get(user=user_1)
        notification        = Notification.get_notification_by_id(
                                    user_1_notification.notification_id,
                                    user_2
                             )

        self.assertIsNone(notification)

    def test_get_notification_stats_method_returns_empty_stats_on_default(self):
        """Test that empty notification statistics return zero values."""

        # no notifications have been sent
        notification_stats = Notification.get_notification_stats(self.user)

        self.assertIsNotNone(notification_stats, "The notificaton stats should not be None")
        self.assertIsInstance(notification_stats, dict, "The returned value should be a dictionary")

        expected_stats = {
            "total": 0,
            "read": 0,
            "unread": 0,
            "today": 0,
        }

        self.assertEqual(notification_stats, expected_stats, "returned dictionary doesn't match expected dictionary")

    def test_get_notification_stats_method_only_returns_current_users_stats(self):
        """Test that notification statistics are isolated to the current user."""

        user_1 = create_user(username="first_username", email="first_user@example.com")
        user_2 = create_user(username="second_username", email="second_user@example.com")

        # Create notifications for user 1
        create_user_notifications(user_1)

        # Retrieve user 1's notification statistics
        user_1_notification_stats = Notification.get_notification_stats(user_1)

        # Verify user 1's notification statistics.
        self.assertEqual(user_1_notification_stats["total"], len(test_cases))
        self.assertEqual(user_1_notification_stats["read"], 3)
        self.assertEqual(user_1_notification_stats["unread"], 2)
        self.assertEqual(user_1_notification_stats["today"], 5)

        user_2_notification_stats = Notification.get_notification_stats(user_2)

        # Verify user 2's statistics remain zero.
        expected_stats = {
                    "total": 0,
                    "read": 0,
                    "unread": 0,
                    "today": 0,
                }

        self.assertEqual(
            user_2_notification_stats,
            expected_stats,
            "User 2's notification statistics should all be zero."
        )

    def test_get_notification_stats_method_only_counts_notifications_created_today(self):
        """Test that today's notification count excludes notifications from other dates."""

        today     = timezone.localdate()
        yesterday = today - timedelta(days=1)
        tomorrow  = today + timedelta(days=1)

        today_start = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )

        yesterday_start = timezone.make_aware(
            datetime.combine(yesterday, datetime.min.time())
        )

        tomorrow_start = timezone.make_aware(
            datetime.combine(tomorrow, datetime.min.time())
        )

        # create notificaton for today
        today_notification = Notification.objects.create(
                                    user=self.user,
                                    notification_type=Notification.NotificationType.CARD_REQUEST_APPROVED,
                                    title=Notification.NotificationTitle.CARD_REQUEST_APPROVED,
                                    message=Notification.NotificationMessage.CARD_REQUEST_APPROVED,
                                    )

        # create a notificaton in the past (yesterday)
        yesterday_notification = Notification.objects.create(
                                    user=self.user,
                                    notification_type=Notification.NotificationType.TRANSFER_RECEIVED,
                                    title=Notification.NotificationTitle.TRANSFER_RECEIVED,
                                    message=Notification.NotificationMessage.TRANSFER_RECEIVED,
                                    )

        # create a notification for tomorrow (1 day)
        tomorrow_notification = Notification.objects.create(
                                    user=self.user,
                                    notification_type=Notification.NotificationType.TRANSFER_SENT,
                                    title=Notification.NotificationTitle.TRANSFER_SENT,
                                    message=Notification.NotificationMessage.TRANSFER_SENT,

                                    )

        today_notification.created_at     = today_start
        yesterday_notification.created_at = yesterday_start
        tomorrow_notification.created_at  = tomorrow_start

        today_notification.save()
        yesterday_notification.save()
        tomorrow_notification.save()

        notification_stats = Notification.get_notification_stats(self.user)

        expected_stats = {
            "total": 3,
            "read": 0,
            "unread": 3,
            "today": 1,
        }

        self.assertEqual(
            notification_stats,
            expected_stats,
            "Notification statistics should only count notifications created today."
        )


class NotificationServiceTest(TestCase):

    def test_get_user_notification_summary_retrieves_and_caches_stats_on_cache_miss(self):
        """Test that notification statistics are retrieved and cached on a cache miss."""

        user = create_user(username="notification_test_user")
        expected_stats = {
            "total": 0,
            "read": 0,
            "unread": 0,
            "today": 0,
        }

        with (
            patch("notification.services.notification_service.get_cache_with_retry", return_value=None) as mock_get_cache,
            patch("notification.services.notification_service.set_cache_with_retry") as mock_set_cache,
            patch.object(Notification, "get_notification_stats", return_value=expected_stats) as mock_get_stats,
        ):

            notification_stats = NotificationService.get_user_notification_summary(user)
            self.assertEqual(notification_stats, expected_stats)

            now = timezone.localdate()

            expected_cache_key = (
                f"notification_summary_{user.pk}_{now.year}_{now.month}_{now.day}"
            )
            mock_set_cache.assert_called_once_with(
                expected_cache_key,
                value=expected_stats,
                ttl=NOTIFICATION_SUMMARY_CACHE_TTL
            )
            mock_get_cache.assert_called_once()
            mock_get_stats.assert_called_once_with(user)

    def test_get_user_notification_summary_returns_cached_stats_on_cache_hit(self):
        """Test that cached notification statistics are returned without querying the database."""

        user = create_user(username="notification_cache_hit_user")

        expected_stats = {
            "total": 5,
            "read": 3,
            "unread": 2,
            "today": 5,
        }

        with (patch("notification.services.notification_service.get_cache_with_retry", return_value=expected_stats) as mock_get_cache,
            patch.object(Notification,"get_notification_stats") as mock_get_stats,
            patch("notification.services.notification_service.set_cache_with_retry") as mock_set_cache,
        ):

            notification_stats = NotificationService.get_user_notification_summary(user)
            self.assertEqual(notification_stats, expected_stats)

            mock_get_cache.assert_called_once()
            mock_get_stats.assert_not_called()
            mock_set_cache.assert_not_called()

    def test_get_user_notification_cache_key_returns_expected_key(self):
        """Test that the notification cache key contains the user's ID and current date."""

        user = create_user(username="notification_cache_key_user")
        now = timezone.localdate()

        expected_cache_key = (f"notification_summary_{user.pk}_{now.year}_{now.month}_{now.day}")

        cache_key = NotificationService._get_user_notification_cache_key(user)
        self.assertEqual(cache_key, expected_cache_key)

    def test_invalidate_user_notification_cache_deletes_user_cache(self):
        """Test that the user's notification summary cache is invalidated."""

        user               = create_user(username="notification_cache_invalidation_user")
        now                = timezone.localdate()
        expected_cache_key = (f"notification_summary_{user.pk}_{now.year}_{now.month}_{now.day}")

        with patch("notification.services.notification_service.delete_cache_with_retry") as mock_delete_cache:

            NotificationService._invalidate_user_notification_cache(user)
            mock_delete_cache.assert_called_once_with(expected_cache_key)

    def test_get_user_notification_summary_rejects_invalid_user(self):
        """Test that an invalid user is rejected when retrieving notification statistics."""

        invalid_user = "not_a_user"

        with self.assertRaises(TypeError):
            NotificationService.get_user_notification_summary(invalid_user)

    def test_get_user_notification_summary_returns_empty_stats_for_user_without_notifications(self):
        """Test that an empty notification summary is returned when the user has no notifications."""

        expected_stats = {'total': 0,
                          'read': 0,
                          'unread': 0,
                          'today': 0
                         }

        user = create_user(
            username="notification_empty_summary_user",
            email="notification_empty_summaary@example.com"
        )

        with patch("notification.services.notification_service.get_cache_with_retry", return_value=None) as mock_get_cache:

            notification_stats = NotificationService.get_user_notification_summary(user)
            self.assertEqual(notification_stats, expected_stats)
            mock_get_cache.assert_called_once()



