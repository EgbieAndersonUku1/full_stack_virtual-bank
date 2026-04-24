from django.urls import path
from . import views

urlpatterns = [
    path('login/', view=views.login_user, name="login_user"),
    path('register/', view=views.register_user, name="register_user"),
    path("username/exists/", view=views.does_username_exists, name="does_username_exists"),
    path("email/exists/", view=views.does_email_exists, name="does_email_exists"),
]