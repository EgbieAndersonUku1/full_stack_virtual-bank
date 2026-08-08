from pycountry import currencies




def get_currencies() -> list[tuple[str, str]]:
    """
    Return a list of tuples containing currency codes and names.
    The first element of the currency is the currency code e.g GBP
    and the second is the name associated with code e.g British pound

    Example:
        [
            ("GBP", "Pound Sterling"),
            ("USD", "US Dollar"),
            ("EUR", "Euro"),
        ]
    """
    return [ (currency.alpha_3, currency.name) for currency in currencies]
