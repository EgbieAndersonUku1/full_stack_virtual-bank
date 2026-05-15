from django.shortcuts import render

# Create your views here.


def employee_services(request):
    return render(request, "staff/employee_services/portal.html")


def work_guidelines(request):
    return render(request, "staff/employee_services/work_place_guidelines.html")