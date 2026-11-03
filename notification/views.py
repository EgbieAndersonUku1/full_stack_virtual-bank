from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from uuid import UUID
from django.core.paginator import Paginator

from setup.decorators import onboarding_required
from utils.decorators import go_to_staff_page, is_email_verified
from notification.services.notification_service import NotificationService
from notification.models import Notification


# Create your views here.

@is_email_verified
@login_required
@onboarding_required
@go_to_staff_page
def notifications_centre(request):

    PER_PAGE    = 25

    all_page_number = request.GET.get("all_page")
    read_page_number = request.GET.get("read_page")
    unread_page_number = request.GET.get("unread_page")

    all_notifications           = Notification.get_notifications_by_user(request.user)
    read_notifications          = all_notifications.filter(is_read=True)
    unread_notifications        = all_notifications.filter(is_read=False)

    all_notifications_paginator    = Paginator(all_notifications, PER_PAGE)
    read_notifications_paginator   = Paginator(read_notifications, PER_PAGE)
    unread_notifications_paginator = Paginator(unread_notifications, PER_PAGE)


    all_notifications_page_object    =  all_notifications_paginator.get_page(all_page_number)
    read_notification_page_object    =  read_notifications_paginator.get_page(read_page_number)
    unread_notifications_page_object =  unread_notifications_paginator.get_page(unread_page_number)

    context = {
        "all_notifications_page_object": all_notifications_page_object,
        "read_notifications_page_object": read_notification_page_object,
        "unread_notifications_page_object": unread_notifications_page_object,
        "notification_types": Notification.NotificationType,
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
