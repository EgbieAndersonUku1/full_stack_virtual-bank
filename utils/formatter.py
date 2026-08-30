from decimal import Decimal


def format_currency(amount: Decimal | None) -> str:
    """
    Format a Decimal monetary amount for presentation.

    Args:
        amount: The monetary amount to format.

    Returns:
        A string containing the amount formatted with comma separators
        and two decimal places.

    Example:
        Decimal("12500.50") -> "12,500.50"

    Raises:
        Raises `decimalInvalidOperation` if the amount being converted
        is the wrong type.
    """
    if amount is None:
        return "0.00"

    amount = Decimal(str(amount))
    return f"{amount:,.2f}"

