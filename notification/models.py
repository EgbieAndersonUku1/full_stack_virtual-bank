from __future__ import annotations
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from uuid import uuid4
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model


from utils.validators.validators import validate_user

User = get_user_model()


# Create your models here.

class Notification(models.Model):
    """
    Represents a notification sent to a user about an important account
    or transaction event.

    Each notification is uniquely identified per user and can represent
    events such as transfers, card requests, and account creation.
    """

    class NotificationType(models.TextChoices):

        TRANSFER_SENT = "transfer_sent", "Transfer sent"
        TRANSFER_RECEIVED = (
            "transfer_received",
            "Transfer amount has been received",
        )

        CARD_REQUEST_APPROVED = (
            "card_request_approved",
            "Card request was approved",
        )
        CARD_REQUEST_REJECTED = (
            "card_request_rejected",
            "Card request was rejected",
        )

        ACCOUNT_CREATED = "account_created", "Account created"

    notification_id   = models.UUIDField(max_length=32)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=32, choices=NotificationType.choices)
    title             = models.CharField(max_length=80)
    message           = models.CharField(max_length=255)
    is_read           = models.BooleanField(default=False)
    read_at           = models.DateTimeField(blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)
    action_url        = models.CharField(max_length=255, blank=True)
    class Meta:

        indexes = [
            # Optimizes queries for a user's read/unread notifications.
            models.Index(
                fields=["user", "is_read"],
                name="notification_user_read_idx",
            ),
        ]

    @classmethod
    def _get_notifications(cls, is_read: bool, user: User) -> QuerySet["Notification"]:
        """
        Return notifications for a user filtered by read status.
        """
        validate_user(user=user)

        if not isinstance(is_read, bool):
            error_msg = _(
                f"The is_read must be a bool. "
                f"Got type {type(is_read).__name__}"
            )
            raise TypeError(error_msg)

        return cls.objects.filter(
            user=user,
            is_read=is_read,
        )

    @classmethod
    def get_read_notifications(cls, user: User) -> QuerySet["Notification"]:
        """Return all read notifications belonging to the user."""

        return cls._get_notifications(
            user=user,
            is_read=True,
        )

    @classmethod
    def get_unread_notifications(cls, user: User) -> QuerySet["Notification"]:
        """Return all unread notifications belonging to the user."""

        return cls._get_notifications(
            user=user,
            is_read=False,
        )

    @classmethod
    def get_notification_by_id(cls, notification_id: str, user: User) -> "Notification | None":
        """
        Return a user's notification by notification ID.

        Returns None if the notification does not exist for the user.
        """
        try:
            return cls.objects.get(
                notification_id=notification_id,
                user=user,
            )
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_unread_notification_count(cls, user: User) -> int:
        """Return the number of unread notifications belonging to the user."""
        return cls.get_unread_notifications(user=user).count()

    @classmethod
    def get_notifications_by_user(cls, user: User) -> QuerySet["Notification"]:
        """Retrieves all notifications for a specific user.

        Args:
            user (User): The user object belong to the user. This will be
                         used to retreive all the user's notifications.

        Raises:
            Raises an error if the user is not a User instance

        """
        validate_user(user)
        return cls.objects.filter(user=user)

    @classmethod
    def get_notification_stats(cls, user: User) -> dict:
        """
        
        """

        # Get the start of today in the user's current timezone
        today_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)

        tomorrow_start = timezone.localtime().replace(hour=0,
                                                      minute=0,
                                                      second=0,
                                                      microsecond=0
                                                    ) + timedelta(days=1)

        stats = Notification.objects.filter(user=user).aggregate(
            total=Count('id'),
            read=Count('id', filter=Q(is_read=True)),
            unread=Count('id', filter=Q(is_read=False)),
            today=Count(
                'id',
                filter=Q(created_at__gte=today_start) & Q(created_at__lt=tomorrow_start)
            )
        )

        return stats

    def save(self, *args, **kwargs):

        if self.notification_id is None:
            self.notification_id = uuid4()

        super().save(*args, **kwargs)


