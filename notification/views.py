from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from uuid import UUID

from setup.decorators import onboarding_required
from utils.decorators import go_to_staff_page, is_email_verified
from notification.services.notification_service import NotificationService


# Create your views here.

@is_email_verified
@login_required
@onboarding_required
@go_to_staff_page
def notifications_centre(request):

    notification_summary = NotificationService.get_user_notification_summary(user=request.user)
    context = {
        "read": notification_summary["read"],
        "unread": notification_summary["unread"],
        "total": notification_summary["total"],
        "today": notification_summary["today"]
    }

    return render(request, "home/notifications/notification_centre.html", context=context)


@is_email_verified
@login_required
@onboarding_required
@go_to_staff_page
def view_notification(request, notification_id: UUID) -> HttpResponse:

    # placeholder for now, notification message will go here
    context = {
        "notification_message": "This page hasn't been build yet, please coming back later"
    }
    return render(request, "home/notifications/notification_message.html", context=context)
