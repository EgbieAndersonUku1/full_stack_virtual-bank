from uuid import uuid4, UUID
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from utils.custom_errors import InvalidNotificationTypeError
from notification.models import Notification
from utils.validators.validators import validate_user
from utils.safe_cache import get_cache_with_retry, set_cache_with_retry, delete_cache_with_retry

User = get_user_model()

NOTIFICATION_SUMMARY_CACHE_TTL = 60 * 60 * 24  # 24 hours


class NotificationService:
    """
    Handles notification-related business operations, including retrieving
    notification summaries and managing cached notification statistics.

    Uses PostgreSQL as the source of truth and Django's cache framework
    to reduce repeated database queries when retrieving notification
    statistics for users.

    Uses the application's current local date to generate cache keys,
    ensuring a new cache entry is used when the date changes.
    """

    @classmethod
    def _get_from_cache_or_from_db(cls, user: User) -> dict:
        """
        Retrieves the user's notification statistics from the cache.

        If the statistics are not cached, retrieves them from the
        database, stores the result in the cache and returns it.

        Args:
            user (User): The user whose notification statistics are required.

        Returns:
            dict: The user's notification statistics.
        """
        cache_key    = cls._get_user_notification_cache_key(user)
        cached_value = get_cache_with_retry(key=cache_key)

        if cached_value is not None:
            return cached_value

        notification_stats = Notification.get_notification_stats(user)
        set_cache_with_retry(cache_key, value=notification_stats, ttl=NOTIFICATION_SUMMARY_CACHE_TTL)
        return notification_stats

    @classmethod
    def _get_user_notification_cache_key(cls, user: User) -> str:
        """
        Generates a cache key using the user's primary key and the current
        local date.

        Including the date ensures a new cache entry is used when the
        application's local date changes.

        Args:
            user (User): The user associated with the cache entry.

        Returns:
            str: The generated cache key.
        """
        now              = timezone.localdate()
        year, month, day = now.year, now.month, now.day
        current_date     = f"{year}_{month}_{day}"

        return f"notification_summary_{user.pk}_{current_date}"

    @classmethod
    def _invalidate_user_notification_cache(cls, user: User) -> None:
        """
        Invalidates the user's cached notification statistics.

        Args:
            user (User): The user whose notification cache should be invalidated.
        """
        cache_key = cls._get_user_notification_cache_key(user)
        delete_cache_with_retry(cache_key)

    @classmethod
    def get_user_notification_summary(cls, user: User) -> dict:
        validate_user(user)
        return cls._get_from_cache_or_from_db(user)

    @classmethod
    def create_account_notification(cls, user: User) -> Notification:
        """
        Create an account-created notification for the specified user.

        The notification is generated during account onboarding and includes
        a link to the relevant destination within the application.

        Args:
            user (User): The user who will receive the notification.

        Returns:
            Notification: The newly created account notification.

        Raises:
            TypeError: If the supplied user is invalid.
        """

        validate_user(user)

        notification_id = uuid4()
        action_url      = reverse("notification_message", kwargs={"notification_id": notification_id})

        notification = Notification.objects.create(
            user=user,
            notification_id=notification_id,
            notification_type=Notification.NotificationType.ACCOUNT_CREATED,
            title=Notification.NotificationTitle.ACCOUNT_CREATED.label,
            message=Notification.NotificationMessage.ACCOUNT_CREATED.label,
            action_url=action_url
        )

        transaction.on_commit(
            lambda: cls._invalidate_user_notification_cache(user)
        )

        return notification

    @classmethod
    def update_unread_notification_to_read(cls, notification: Notification) -> Notification | None:
        """
        Mark an unread notification as read and invalidate the user's notification cache.

        If the notification is already marked as read, it is returned without
        modification. Otherwise, its read status and timestamp are updated,
        the changes are saved, and the user's notification cache is invalidated
        to ensure subsequent requests retrieve fresh data.

        Args:
            notification (Notification): The notification instance to mark as read.

        Returns:
            Notification | None: The updated notification instance, or None if
                the save operation does not return a notification.

        Raises:
            InvalidNotificationTypeError: If the provided notification is not
                an instance of Notification.
        """

        if not isinstance(notification, Notification):
            error_msg = _(
                f"notification is not an instance of Notification",
                f"Expected type notification got {type(notification).__name__}"
            )
            raise InvalidNotificationTypeError(error_msg)

        if notification.is_read:
            return notification

        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()

        # invalidate the cache, this will force it to get/create a new cache entry when the app calls `get_user_notification_summary(...)`
        cls._invalidate_user_notification_cache(notification.user)

        return notification






