from django.urls import path
from . import views

urlpatterns = [
    path('login/', view=views.login_user, name="login_user"),
    path('logout/', view=views.logout_user, name="logout_user"),
    path('register/', view=views.register_user, name="register_user"),
    path("username/exists/", view=views.does_username_exists, name="does_username_exists"),
    path("email/exists/", view=views.does_email_exists, name="does_email_exists"),
    path("terms-and-conditions/", view=views.terms_and_conditions, name="terms_and_conditions"),
    path("verify-registration-code/", view=views.verify_registration_code, name="confirm_registration_code"),
    path("resend-verification-code/", view=views.request_email_verification_code, name="resend_verification_code"),
    
]