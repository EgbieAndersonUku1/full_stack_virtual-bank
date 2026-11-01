import uuid
from django.test import TestCase
from notification.models import Notification
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone
from django.db import IntegrityError, transaction


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


