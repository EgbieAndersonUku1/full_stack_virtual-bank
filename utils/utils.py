from django.utils.translation import gettext_lazy as _

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