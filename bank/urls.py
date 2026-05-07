from django.urls import path

from . import views


urlpatterns = [
   
   path("add_bank/", view=views.add_bank, name="add_bank"),
   path("bank_operation_centre/", view=views.bank_operation_centre, name="bank_operation_centre"),
   
]
