
from decimal import InvalidOperation, Decimal
from datetime import datetime, date
from django.utils.translation import gettext_lazy as _



def convert_amount_to_decimal(amount: int | float) -> Decimal | None:
    """
    Convert a numeric funding amount to ``Decimal``.

    The amount is first converted to a string before being passed to
    ``Decimal`` to avoid floating-point precision issues.

    Args:
        amount: The amount supplied by the user.

    Returns:
        A ``Decimal`` representation of the amount, or ``None``
            if the amount cannot be converted to ``Decimal``.
    """

    try:
        return Decimal(str(amount))
    except InvalidOperation as e:
        raise InvalidOperation(str(e))


def convert_date_string_to_date_object(date_string: str) -> date:
    """Convert a YYYY-MM-DD date string to a datetime.date object.

    Args:
        date_string: A date string in YYYY-MM-DD format.
            Expected format: "YYYY-MM-DD", e.g. "2026-10-01".

    Returns:
        A datetime.date object representing the given date.

    Raises:
        TypeError: If date_string is not a string.
        ValueError: If date_string is not a valid date in YYYY-MM-DD format.

    Examples:
        >>> convert_date_string_to_date_object("2026-10-01")
        datetime.date(2026, 10, 1)
    """
    if not isinstance(date_string, str):
        error_msg = "Date must be a string, got type {}".format(type(date_string).__name__)
        raise TypeError(_(error_msg))

    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        error_msg = "Date string must be a valid YYYY-MM-DD date, got {}".format(date_string)
        raise ValueError(
           _(error_msg)
        )
