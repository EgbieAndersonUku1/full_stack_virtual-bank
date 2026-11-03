

from notification.services.notification_service import NotificationService


def get_notification_cards_status(request):
    """
    Retrieve notification summary counts for the authenticated user.

    Returns an empty dictionary if the request is missing or the user
    is not authenticated. Otherwise, returns the user's read, unread,
    total and today's notification counts.
    """

    if not request or not request.user.is_authenticated:
        return {}

    notification_summary = NotificationService.get_user_notification_summary(user=request.user)
    
    return {
            "read": notification_summary["read"],
            "unread": notification_summary["unread"],
            "total": notification_summary["total"],
            "today": notification_summary["today"],

        }
