from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from utils.decorators import is_email_verified

# Create your views here.

@is_email_verified
@login_required
def bank_setup_welecome(request):
    return render(request, "bank/setup/welcome.html")



@is_email_verified
@login_required
def bank_setup_pin(request):
    return render(request, "bank/setup/bank-pin-setup.html")



@is_email_verified
@login_required
def bank_setup_bank_choices(request):
    return render(request, "bank/setup/bank-choices.html")


@is_email_verified
@login_required
def bank_setup_completion(request):
    return  render(request, "bank/setup/bank-completion.html")