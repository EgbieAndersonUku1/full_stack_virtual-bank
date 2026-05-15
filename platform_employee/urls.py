from django.urls import path

from . import views



urlpatterns = [

    path("portal/services", view=views.employee_services, name="employee_services"),
    
   
]
