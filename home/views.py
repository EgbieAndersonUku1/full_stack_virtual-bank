from django.shortcuts import render

# Create your views here.



def bank_home(request):
    return render(request, "home/bank/virtual-bank.html")



def dashboard(request):
    return render(request, "home/dashboard/dashboard.html")



def money_transfer(request):
    return render(request, "home/dashboard/money_transfer.html")