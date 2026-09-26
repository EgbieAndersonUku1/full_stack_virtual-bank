
import logging
from django.contrib.auth import get_user_model
from decimal import Decimal, InvalidOperation
from django.utils.translation import gettext_lazy as _

from bank.services.bank_services import BankAccountCacheService
from bank.services.transaction_services import Status, Start


logger = logging.Logger(__name__)

User = get_user_model()


def transfer_error_response(message: str, action: str,  user: User):
    """
    Build a standard unsuccessful response for transfer errors.

    This helper keeps the error response structure consistent across expected
    transfer validation failures handled by the transfer view.

    Args:
        message (str): A user-facing message describing the transfer error.
        action (str): A short action or error identifier describing the type
                    of transfer failure.

        Returns:
            dict: A transfer error response containing the unsuccessful status,
                  error message, action, zero transfer amount, empty transfer
                reference, and the user's current total account balance.
    """
    return {
            "SUCCESS": False,
            "MSG": message,
            "ACTION": action,
            "STATUS": Status.UNSUCCESSFUL.value,
            "AMOUNT": Decimal("0.00"),
            "TRANSFER_REFERENCE": "",
            "BALANCE": BankAccountCacheService.get_total_account_balance(user),
        }



def parse_transfer_amount(data: dict) -> Decimal:
    amount = data["amount"]

    try:
        return Decimal(amount)
    except (InvalidOperation, TypeError, ValueError):
        error_msg = _("Invalid transfer amount")
        raise ValueError(error_msg)


def map_transfer_start_to_enum(data: dict):
    """
    Maps the transfer start value from the input data to its corresponding

    Start enum member.

        Args:
            data: A dictionary containing the "transferStart" value.

    Returns:
        The corresponding Start enum member.
    """
    transfer_start = data["transferStart"]

    if not isinstance(transfer_start, str):
        error_msg = f"Expected a string got type {type(transfer_start).__name__}"
        raise AttributeError(_(error_msg))

    value = transfer_start.lower()

    mapping = {
            "immediately": Start.IMMEDIATELY,
            "schedule_date": Start.SCHEDULED,
        }

    return mapping[value]


def validate_required_keys(data: dict):
    required_keys = {
            "bankTransferSelection",
            "amount",
            "transferStart",
            "pin",
        }

    missing_keys = required_keys - data.keys()

    if missing_keys:
        error_msg = f"Missing required keys: {', '.join(missing_keys)}"

        logger.debug(
                f"Required transfer data was not sent to the backend: {missing_keys}"
            )

        raise KeyError(_(error_msg))
