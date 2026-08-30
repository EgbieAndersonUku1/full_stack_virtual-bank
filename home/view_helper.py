from decimal import Decimal,InvalidOperation

from django.utils.translation import gettext_lazy as _

from utils.formatter import format_currency
from utils.validators.validators import validate_dict



def format_balance_fields(data: dict) -> None:
    """
    Format monetary balance fields in a response for presentation.

    The supplied response dictionary must contain the expected balance
    fields. Each balance is formatted with comma separators and two
    decimal places.

    Args:
        data (dict): Response data containing the account balance fields.

    Raises:
        TypeError: If ``data`` is not a dictionary.
        KeyError: If a required balance field is missing.
    """

    if not isinstance(data, dict):
        error_msg = "Expected a dict, got type {}".format(type(data).__name__)
        raise TypeError(_(error_msg))

    required_keys = (
        "CURRENT_ACCOUNT_BALANCE",
        "SAVINGS_ACCOUNT_BALANCE",
        "TOTAL_BALANCE",
        "BALANCE",
    )

    for key in required_keys:
        if key not in data:
            error_msg = "Required key '{}' is missing from the response.".format(key)
            raise KeyError(_(error_msg))

    for key in required_keys:
        try:
            data[key] = format_currency(data[key])
        except InvalidOperation:
            pass


def extract_pin_from_dict(data: dict) -> str | None:
    """
    Extracts a pin string from a dictinary object.

    The function takes a dictionary object and extracts
    a pin if found. If no pin is found returns None.

    Args:
        data (dict): A dictionary object contain the pin string

    Returns:
        A pin in the form of a string or none if not found.

    """
    validate_dict(data)
    return data.get("pin", {}).get("values")



def extract_amount_from_dict(data: dict) -> Decimal | None:
    """
    Extract the amount from a dictionary and return it as a Decimal.

    Args:
        data: Dictionary containing an amount value.

    Returns:
        The amount as a Decimal, or None if no amount is present.
    """
    validate_dict(data)

    amount = data.get("amount")

    if amount is None or amount == "":
        return None

    return Decimal(str(amount))
