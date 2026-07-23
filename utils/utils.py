from django.utils.translation import gettext_lazy as _

from utils.custom_errors import IncorrectAddressPartTypeError

# -------------------------------------------------------------------
# utils.py
#--------------------------------------------------------------------
import logging

class RightIndentedFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):

        # Add a custom indent to the beginning of the log message
        original_message = super().format(record)
        return f"    {original_message}"  # 4 spaces or any amout of space you want




def validate_params_are_strings(params: dict) -> None:
    """
    Ensure all values in the provided dictionary are strings.

    This function iterates through a dictionary of parameters and validates that
    each value is of type `str`. If any value is not a string, a ValueError is raised
    identifying the offending parameter and its actual type.

    Args:
        params (dict): A dictionary of key-value pairs to validate.

    Raises:
        ValueError: If any value in `params` is not a string.

    Example:
        params = {"name": "John", "city": "London"}
        validate_params_are_strings(params)
    """

    if not isinstance(params, dict):
        raise TypeError(_("The params must be a dictionary"))

    for name, value in params.items():
        if not isinstance(value, str):
            raise ValueError(
                _(f"Expected '{name}' to be a string but got {type(value).__name__}")
            )



def format_full_address(address_1: str,
                        city: str,
                        postcode: str,
                        country: str,
                        *,
                        address_2: str | None = None,
                        county: str | None = None) -> str | None:
    """
    Build a formatted postal address from individual address components.

    Required address components must be provided to construct the address.
    Optional components are keyword-only and are included only when supplied.

    The returned address is formatted as a comma-separated string suitable
    for display within the application.

    Args:
        address_1 (str):
            The first line of the address.

        city (str):
            The city or town.

        postcode (str):
            The postal or ZIP code.

        country (str):
            The country name.

        address_2 (str | None):
            The second line of the address. Must be supplied as a keyword
            argument. Defaults to ``None``.

        county (str | None):
            The county or administrative region. Must be supplied as a
            keyword argument. Defaults to ``None``.

    Returns:
        str | None:
            A formatted address string if the required address components are
            provided; otherwise, ``None``.

    Raises:
        IncorrectAddressPartTypeError:
            Raised if any supplied address component is not a string.
    """

    if not (address_1 and city and postcode and country):
        return

    address_parts_list = [
        ("address_1", address_1),
        ("address_2", address_2),
        ("city", city),
        ("county", county),
        ("postcode", postcode),
        ("country", country),
    ]
    cleaned_address_parts = []

    for (identifier, address_part) in address_parts_list:

        if address_part is None:
            continue

        if not isinstance(address_part, str):
            error_msg = _("One of the address part - <{identifier}> is not a string. " \
            "             Got type {address_part}".format(identifier=identifier,
                                                          address_part=type(address_part).__name__)
                                                          )
            raise IncorrectAddressPartTypeError(error_msg)

        cleaned_address_parts.append(address_part)

    if len(cleaned_address_parts) == 0:
        return

    return ', '.join(cleaned_address_parts)
    



def format_boolean_as_text(value: bool) -> str:
    """
    Convert a boolean value into a human-readable text representation.

    Args:
        value (bool):
            The boolean value to convert.

    Returns:
        str:
            Returns "Yes" when the value is True, otherwise "No".
    """
    return "Yes" if value else "No"
