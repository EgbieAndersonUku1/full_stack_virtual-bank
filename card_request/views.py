from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from setup.decorators import onboarding_required
from utils.decorators import go_to_staff_page, is_email_verified

# Create your views here.




@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def card_request_information(request):
    return render(request, "card_request/user/card-request-information.html")