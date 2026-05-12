from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from utils.decorators import has_superuser_permissions
from .services import BankProvisioningService

from bank.forms import AddBankForm


# Create your views here.

@has_superuser_permissions
@login_required
def add_bank(request):

    form = AddBankForm()
    if request.method == "POST":
        form = AddBankForm(request.POST, request.FILES)

        if form.is_valid():
            cleaned_bank_data = form.cleaned_data.copy()
            BankProvisioningService.create_bank(cleaned_bank_data)
            messages.success(request, _("Bank created successfully"))
            return redirect("add_bank")
        
        messages.error(request, _("We couldn't add the bank. Please correct the highlighted errors and try again."))
    context = {
        "form": form
    }
    return render(request, "bank/bank_creation/add_bank.html", context=context)


@has_superuser_permissions
@login_required
def bank_operation_centre(request):
    return render(request, "bank/bank_creation/bank_operation_centre.html")