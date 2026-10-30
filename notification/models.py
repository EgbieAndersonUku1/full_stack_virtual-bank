from __future__ import annotations

from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from enum import Enum


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

    notification_id   = models.CharField(max_length=32)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=32, choices=NotificationType.choices)
    title             = models.CharField(max_length=80)
    message           = models.CharField(max_length=255)
    is_read           = models.BooleanField(default=False)
    read_at           = models.DateTimeField(blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [

            models.UniqueConstraint(
                fields=["notification_id", "user"],
                name="unique_notification_per_user",
            ),
        ]
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


