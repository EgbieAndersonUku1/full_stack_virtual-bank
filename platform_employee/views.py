from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from utils.decorators import has_permissions_to_view_page


# Create your views here.

@login_required
@has_permissions_to_view_page
def employee_services(request):
    return render(request, "staff/employee_services/portal.html")


@login_required
@has_permissions_to_view_page
def work_guidelines(request):
    return render(request, "staff/employee_services/work_place_guidelines.html")
