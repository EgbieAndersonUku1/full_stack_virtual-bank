from django.urls import path

from . import views



urlpatterns = [
    path('card-request-information/', view=views.card_request_information, name="card_request_information"),
   
]
