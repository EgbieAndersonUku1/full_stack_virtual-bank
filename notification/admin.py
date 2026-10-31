from django.contrib import admin

from notification.models import Notification

# Register your models here.

class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "notification_id",
        "user",
        "notification_type",
        "title",
        "is_read",
        "read_at",
        "created_at",
        "updated_at",
    ]

    list_per_page = 25

    readonly_fields = [
        "notification_id",
        "title",
        "notification_type",
        "message",
        "is_read",
        "read_at",
        "action_url",
        "created_at",
        "updated_at",
    ]

    list_display_links = ["notification_id"]

    fieldsets = (
        (
            "Notification Information",
            {
                "description": (
                    "Displays the notification's unique identifier, "
                    "associated user, notification type, title, message, "
                    "and associated action URL."
                ),
                "fields": [
                    "notification_id",
                    "user",
                    "notification_type",
                    "title",
                    "message",
                    "action_url",
                ],
            },
        ),
        (
            "Read Status",
            {
                "description": (
                    "Indicates whether the notification has been read "
                    "and records when it was marked as read."
                ),
                "fields": [
                    "is_read",
                    "read_at",
                ],
            },
        ),
        (
            "Audit Information",
            {
                "description": (
                    "Tracks the date and time the notification was "
                    "created and most recently updated."
                ),
                "fields": [
                    "created_at",
                    "updated_at",
                ],
            },
        ),
    )


admin.site.register(Notification, NotificationAdmin)
