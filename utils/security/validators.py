from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


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
