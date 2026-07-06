from django.urls import path

from . import views



urlpatterns = [
    path('card-request-information/', view=views.card_request_information, name="card_request_information"),
    path('card-request-employment/', view=views.card_request_employment, name="card_request_employment"),
    path('review-and-confirm/', view=views.card_request_review_and_confirm, name="card_request_review_and_confirm" )
   
]
