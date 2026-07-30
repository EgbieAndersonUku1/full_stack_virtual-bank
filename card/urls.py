
from django.urls import path

from . import views


urlpatterns = [
    path("add-to-dashboard/", views.update_card_dashboard_display, name="update_card_dashboard_display"),
]
