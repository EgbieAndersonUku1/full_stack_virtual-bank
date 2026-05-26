from django.urls import path

from . import views


urlpatterns = [

    path("welcome/", view=views.bank_setup_welecome, name="setup_welcome"),
    path("bank/choices/", view=views.bank_setup_bank_choices, name="choose_bank"),
    path("add-pin/", view=views.bank_setup_pin, name="choose_pin"),
    path("create/profile", view=views.bank_setup_create_profile, name="create_profile"),
    path("confirmation-step/", view=views.bank_setup_final_confirmation, name="bank_confirmation"),
    path("account/creation/", view=views.create_bank_account, name="create_account"),
    path("upload/cropped/image/", view=views.upload_profile_picture, name="upload_crop_image"),

]
