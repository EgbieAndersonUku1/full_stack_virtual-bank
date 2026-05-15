from django.urls import path

from . import views



urlpatterns = [

    path("portal/services/", view=views.employee_services, name="employee_services"),
    path("portal/services/work-guidelines-and-policies/", view=views.work_guidelines, name="work_guidelines"),
    
   
]
