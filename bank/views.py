from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from utils.decorators import has_superuser_permissions

# Create your views here.

@has_superuser_permissions
@login_required
def add_bank(request):
    return render(request, "bank/bank_creation/add_bank.html")


@has_superuser_permissions
@login_required
def bank_operation_centre(request):
    return render(request, "bank/bank_creation/bank_operation_centre.html")