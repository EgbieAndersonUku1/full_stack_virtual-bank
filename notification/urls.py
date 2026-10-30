from django.urls import path

from . import views


urlpatterns = [

   path("centre/", view=views.notifications_centre, name="notification_centre")
]
