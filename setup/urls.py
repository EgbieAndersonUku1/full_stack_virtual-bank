from django.urls import path

from . import views


urlpatterns = [
    path('setup/', view=views.setup, name="setup"),
]
