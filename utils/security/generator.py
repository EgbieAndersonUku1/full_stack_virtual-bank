import secrets

from django.utils.translation import gettext_lazy as _


def generate_secure_code(code_length: int = 12) -> str:
    """
    Generate a cryptographically secure numeric verification code.

    This function creates a random code consisting only of digits (0–9),
    using a cryptographically secure random number generator. The length
    of the code can be configured via the ``code_length`` parameter.

    Args:
        code_length (int, optional):
            The number of digits to include in the generated code.
            Defaults to 12.

    Returns:
        str:
            A randomly generated numeric string of length ``code_length``.

    Raises:
        TypeError:
            If ``code_length`` is not an integer.

    Notes:
        - This function uses ``secrets.randbelow`` for secure randomness,
          making it suitable for verification codes, OTPs, and tokens.
        - The output is numeric-only for simplicity and compatibility
          with input fields such as SMS or email verification forms.
        - The maximum length that a code can be is 250, anything longer than that
          will throw an error. This is to avoid abuse of secure code generator.

    Example:
        >>> generate_secure_code(6)
        '483920'
    """

    MAXIMUM_CODE_LENGTH = 250

    if not(isinstance(code_length, int)):
        raise TypeError(_(f"The code length is not an integer. Expected an int got value with type {type(code_length).__name__}"))
    
    if code_length <= 0:
        raise ValueError(_("Code length must be greater than 0."))
    
    if code_length > MAXIMUM_CODE_LENGTH:
        raise ValueError(_("Code length must not be greater than 250."))    
    
    MAXIMUM_DIGITS = 10
    return "".join([str(secrets.randbelow(MAXIMUM_DIGITS)) for _ in range(code_length)])