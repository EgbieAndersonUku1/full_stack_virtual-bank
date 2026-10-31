
from django.contrib.auth import get_user_model
from django.utils import timezone

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
        set_cache_with_retry(cache_key, value=notification_stats,  ttl=NOTIFICATION_SUMMARY_CACHE_TTL)
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
    def get_user_notification_summary(cls, user: User):
        validate_user(user)
        return cls._get_from_cache_or_from_db(user)








