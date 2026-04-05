from django.urls import path
from . import views




urlpatterns = [
    path('', views.core_admin, name='core_admin'),
]