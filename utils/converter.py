
from decimal import InvalidOperation, Decimal


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
