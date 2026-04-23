from django.urls import path

from . import views


urlpatterns = [

    path("welcome/", view=views.bank_setup_welecome, name="setup_welcome"),
    path("bank/choices/", view=views.bank_setup_bank_choices, name="choose_bank"),
    path("add-pin/", view=views.bank_setup_pin, name="choose_pin"),
    path("completion/", view=views.bank_setup_completion, name="bank_completion")

]
