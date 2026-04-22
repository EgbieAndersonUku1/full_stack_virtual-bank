from django.shortcuts import render

# Create your views here.



def bank_home(request):
    return render(request, "home/bank/virtual-bank.html")



def dashboard(request):
    return render(request, "home/dashboard/dashboard.html")


def money_transfer(request):
    return render(request, "home/dashboard/money_transfer.html")


def manage_credit_cards(request):
    return render(request, "home/dashboard/manage_cards.html")


def manage_admin(request):
    return render(request, "home/dashboard/admin/admin.html")


def manage_settings(request):
    return render(request,  "home/dashboard/settings.html")