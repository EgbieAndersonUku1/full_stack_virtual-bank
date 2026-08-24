from utils.formatter import format_currency


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
        raise TypeError(
            f"Expected a dict, got type {type(data).__name__}"
        )

    required_keys = (
        "CURRENT_ACCOUNT_BALANCE",
        "SAVINGS_ACCOUNT_BALANCE",
        "TOTAL_BALANCE",
        "BALANCE",
    )

    for key in required_keys:
        if key not in data:
            raise KeyError(f"Required key '{key}' is missing from the response.")

    for key in required_keys:
        data[key] = format_currency(data[key])
