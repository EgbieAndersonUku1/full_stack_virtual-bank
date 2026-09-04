from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import datetime
from decimal import Decimal


from utils.custom_errors import (IncorrectAmountError,
                                IncorrectAmountTypeError,
                                DateTimeError
                                )


User = get_user_model()


def validate_user(user: User) -> None:
    """
    Validate that the supplied value is a Django user instance.

    Args:
        user: The user object to validate.

    Raises:
        TypeError: If the supplied value is not a User instance.
    """

    if not isinstance(user, User):
        error_msg = (
            f"Expected a user instance, got object with type "
            f"{type(user).__name__}"
        )
        raise TypeError(_(error_msg))



def validate_amount(amount: Decimal) -> None:
    """
    Validate that an amount is a positive Decimal value.

    Args:
        amount (Decimal): The monetary amount to validate.

    Raises:
        IncorrectAmountTypeError: If ``amount`` is not a Decimal.
        IncorrectAmountError: If ``amount`` is less than or equal to zero.
    """

    if not isinstance(amount, Decimal):
        error_msg = _(
            "Expected a Decimal. Got type {}".format(
                type(amount).__name__
            )
        )
        raise IncorrectAmountTypeError(error_msg)

    if amount <= Decimal("0"):
        error_msg = _(
            "Amount must be greater than 0. Got amount {}".format(
                amount
            )
        )
        raise IncorrectAmountError(error_msg)



def validate_dict(data: dict) -> None:
    """
    Validate that the supplied value is a dictionary.

    Args:
        data (dict): The value to validate.

    Raises:
        TypeError: If ``data`` is not a dictionary.
    """

    if not isinstance(data, dict):
        error_msg = (
            f"Expected a dict, got type {type(data).__name__}"
        )
        raise TypeError(_(error_msg))



def validate_datetime(date: datetime):

    if not isinstance(date, datetime):
        error_msg = (
            f"Expected a datetime, got type {type(data).__name__}"
        )
        raise DateTimeError(_(error_msg))


