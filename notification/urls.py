from django.urls import path

from . import views


urlpatterns = [

   path("centre/", view=views.notifications_centre, name="notification_centre"),
   path("centre/notification/<uuid:notification_id>/", view=views.view_notification, name="notification_message")

]
