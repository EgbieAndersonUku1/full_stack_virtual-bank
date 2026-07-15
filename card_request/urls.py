from django.urls import path
from . import views


urlpatterns = [
    path('card-request-information/', view=views.card_request_information, name="card_request_information"),
    path('card-request-employment/', view=views.card_request_employment, name="card_request_employment"),
    path('review-and-confirm/', view=views.card_request_review_and_confirm, name="card_request_review_and_confirm" ),
    path('agreement/', view=views.card_request_agreement, name="card_request_agreement" ),
    path('is_all_stages_complete/', view=views.get_card_request_completion_status, name="get_card_request_completion_status"),
    path("application_status/", view=views.is_application_pending, name="application_status"),
    path("all_card_requests/", view=views.card_request_review_queue, name="card_requests_queue"),
    path("all_card_request_dashboard", view=views.all_card_requests_overview, name="card_requests_dashboard"),

    # card applications
    path("all_applications", view=views.all_cards_applications, name="all_applications"),
    path("approved_applications", view=views.approved_applications, name="approved_applications"),
    path("cancelled_applications", view=views.cancelled_applications, name="cancelled_applications"),
    path("on_hold_applications", view=views.on_hold_applications, name="on_hold_applications"),
    path("pending_applications", view=views.pending_applications, name="pending_applications"),
    path("rejected_applications", view=views.rejected_applications, name="rejected_applications"),
    path("under_review_applications", view=views.under_review_applications, name="under_review_applications"),
    path("withdrawn_applications", view=views.withdrawn_applications, name="withdrawn_applications"),



]
