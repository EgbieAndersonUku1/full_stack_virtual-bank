from django.shortcuts import render

# Create your views here.


def bank_setup_welecome(request):
    return render(request, "bank/setup/welcome.html")


def bank_setup_pin(request):
    return render(request, "bank/setup/bank-pin-setup.html")


def bank_setup_bank_choices(request):
    return render(request, "bank/setup/bank-choices.html")


def bank_setup_completion(request):
    return  render(request, "bank/setup/bank-completion.html")