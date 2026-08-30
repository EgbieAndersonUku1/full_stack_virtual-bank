from decimal import Decimal

from django import template

from utils.formatter import format_currency


register = template.Library()


@register.filter
def format_field_currency(amount: Decimal | None):
    """
    Format a monetary amount for display in a Django template.

    This function exposes format_currency() as a Django
    template filter.
    """

    return format_currency(amount)

