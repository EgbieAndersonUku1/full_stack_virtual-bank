import logging

from bank.services.services import BankAccountCacheService
from bank.utils import get_account_context
from card_request.services import CardRequestsApplicationCacheService
from utils.custom_errors import ProfileNotFoundError

logger = logging.getLogger(__name__)


def display_bank_details_on_card(request):

    if not request.user.is_authenticated:
        return {"current_account": None}

    try:

        context = {}
        bank_account = BankAccountCacheService.get_current_account(request.user)
        context.update(get_account_context(bank_account))
        return context

    except ProfileNotFoundError:
        return {}


def safe_context_processor(request, context_builder):
    """
    Safely execute a context builder function.

    Ensures context processors only run for authenticated users and prevents
    exceptions from breaking template rendering.

    Args:
        request: The current HTTP request.
        context_builder (callable): Function responsible for creating the
            context dictionary.

    Returns:
        dict: Context data or an empty dictionary if the user is not
        authenticated or an error occurs.
    """

    if not request.user.is_authenticated:
        return {}

    try:
        return context_builder()

    except Exception:
        logger.exception("Failed to build context processor data.")
        return {}


def display_application_summary_details(request):
    return safe_context_processor(
        request,
        lambda: {
            "basic_information": request.session.get("basic_request"),
        },
    )


def get_application_status_count(request):
    return safe_context_processor(
        request,
        lambda: {
            "application_status": (
                CardRequestsApplicationCacheService.get_applications_status_count()
            ),
        },
    )
