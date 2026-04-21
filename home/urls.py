from django.urls import path

from . import views



urlpatterns = [

    path('', view=views.bank_home, name="bank_home"),
    path('bank/', view=views.bank_home, name="bank_home"),
    path("dashboard/", view=views.dashboard, name="dashboard"),
    path("dashboard/money/transfer/", view=views.money_transfer, name="money_transfer"), 
   
]
