from django import template

from utils.utils import remove_under_score as _remove_under_score

register = template.Library()


@register.filter
def remove_under_score(value):
   return _remove_under_score(value)

