from django.urls import path

from . import views



urlpatterns = [

    path('', view=views.bank_home, name="bank_home"),
    path('bank/', view=views.bank_home, name="bank_home"),

   
]
