from django import template

from utils.formatter import format_currency

register = template.Library()


@register.filter
def format_field_currency(value):
    if value is None:
        return
    if isinstance(value, str):
        return 
    return format_currency(value)

