from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from utils.decorators import is_email_verified, go_to_staff_page

# Create your views here.

@go_to_staff_page
@is_email_verified
def bank_home(request):
    return render(request, "home/bank/virtual-bank.html")

@go_to_staff_page
@is_email_verified
@login_required
def dashboard(request):
    return render(request, "home/dashboard/dashboard.html")


@go_to_staff_page
@is_email_verified
@login_required
def money_transfer(request):
    return render(request, "home/dashboard/money_transfer.html")


@go_to_staff_page
@is_email_verified
@login_required
def manage_credit_cards(request):
    return render(request, "home/dashboard/manage_cards.html")


@is_email_verified
@login_required
def manage_admin(request):
    return render(request, "home/dashboard/admin/system_tools.html")


@login_required
def manage_settings(request):
    return render(request,  "home/dashboard/settings.html")