import logging

from django.db import transaction
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect


from authentication.view_helper import handle_json_post_request
from bank.services.services import BankAccountCacheService
from card.models import CardDashboard, BankCard

# Create your views here.

logger = logging.Logger(__name__)


@login_required
@csrf_protect
def update_card_dashboard_display(request):
    """
    Add or remove a user's bank card from the dashboard.
    The request must contain a valid card number and a boolean
    indicating whether the card should be displayed on the dashboard.
    The card must belong to the authenticated user's bank account.
    When adding a card, the dashboard's maximum card limit is enforced.

    """

    def construction_frontend_message(action):
        if action:
            return "Card added to your dashboard"
        return "Card removed from your dashboard"

    def validate_dashboard_request_types(
        card_number: str,
        add_card_to_dashboard: bool,
    ):
        """
        Validate the types of values received from the dashboard request.

        Args:
            card_number: The card number received from the request.
            add_card_to_dashboard: Indicates whether the card should be
                displayed on the dashboard.

        Returns:
            A tuple containing a boolean indicating whether the received
            values are valid and a dictionary containing any validation
            error messages.
        """
        is_data_received_valid = True
        data = {}

        if not isinstance(add_card_to_dashboard, bool):
            data["ERROR_MSG"] = {
                "DISPLAY_ERROR": (
                    "Expected a boolean object but got type {} with value {value}".format(
                        type(add_card_to_dashboard).__name__,
                        value=add_card_to_dashboard
                    )
                )
            }
            is_data_received_valid = False

        if not isinstance(card_number, str):
            data["ERROR_MSG"] = {
                "CARD_NUMBER_ERROR": (
                    "Expected a string but got type {}".format(
                        type(card_number).__name__
                    )
                )
            }
            is_data_received_valid = False

        return is_data_received_valid, data

    def handle_card_dashboard_display(request_body):
        """
        Add or remove a bank card from the authenticated user's dashboard.
        Validates the request data, verifies that the requested card belongs to
        the user's bank account, enforces the dashboard card limit when adding a card,
        and updates the card's dashboard display status.

        Args:
            request_body: Parsed request data containing the card number and dashboard display status.

        Returns: A dictionary containing the operation status, any error messages, and the
        current number of cards displayed on the dashboard.

        """
        data = {
            "ERROR_MSG": {},
            "SUCCESS": False,
            "SUCCESS_MSG": "",

        }
        add_user_card_to_dashboard = request_body.get("display_in_dashboard")
        card_number                = request_body.get("card_number")

        is_valid, response_dict = validate_dashboard_request_types(card_number, add_user_card_to_dashboard)

        if not is_valid:
            data.update(response_dict)
            return data

        bank_account = BankAccountCacheService.get_current_account(user=request.user)
        card         = BankCard.get_by_bank_account_and_card_number(card_number=card_number, bank_account=bank_account)

        if card is None:
            data["ERROR_MSG"] = "The card number is invalid"
            return data

        with transaction.atomic():

            try:
                card_dashboard = (
                    CardDashboard.objects
                    .select_for_update()
                    .get(bank_account=bank_account)
                )
            except CardDashboard.DoesNotExist:
                logger.critical(
                    "CardDashboard missing for bank account %s. "
                    "This may be an existing account created before CardDashboard "
                    "was introduced. Recreating record.",
                    bank_account.pk
                )
                CardDashboard.objects.create(bank_account=bank_account)


            # Count current dashboard cards to enforce the maximum.
            displayed_card_count = BankCard.get_num_of_cards_in_dashboard(bank_account)

            if (add_user_card_to_dashboard and displayed_card_count >= card_dashboard.max_cards_to_show):
                data["ERROR_MSG"] = (
                    "The dashboard is full. Remove a card before adding a new one."
                )
                return data

            card.show_in_dashboard = add_user_card_to_dashboard
            card.save(update_fields=["show_in_dashboard", "last_modified_on"])

            # Recount after the update so the response contains the current total.
            displayed_card_count = BankCard.get_num_of_cards_in_dashboard(bank_account)

            data["SUCCESS"]                   = True
            data["SUCCESS_MSG"]               = construction_frontend_message(add_user_card_to_dashboard)
            data["NUM_OF_CARDS_IN_DASHBOARD"] = displayed_card_count
            data["ACTION"]                    = "Added Card" if add_user_card_to_dashboard else "Removed Card"
            return data

    return handle_json_post_request(request, func=handle_card_dashboard_display)
