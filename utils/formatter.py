from decimal import Decimal


def format_currency(amount: Decimal) -> str:
    """
    Format a Decimal monetary amount for presentation.

    Args:
        amount: The monetary amount to format.

    Returns:
        A string containing the amount formatted with comma separators
        and two decimal places.

    Example:
        Decimal("12500.50") -> "12,500.50"
    """
    return f"{amount:,.2f}"
