from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

from setup.decorators import onboarding_required
from utils.decorators import go_to_staff_page, is_email_verified


# Create your views here.

@is_email_verified
@onboarding_required
@go_to_staff_page
@login_required
def notifications_centre(request):
    return render(request, "home/notifications/notification_centre.html")



