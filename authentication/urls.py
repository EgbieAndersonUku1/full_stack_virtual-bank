from django.urls import path
from . import views

urlpatterns = [
    path('login/', view=views.login_user, name="login_user"),
    path('register/', view=views.register_user, name="register_user")
]