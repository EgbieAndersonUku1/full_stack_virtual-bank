from django import template

register = template.Library()


@register.filter
def remove_under_score(value):
    if value is None:
        return ""
    return " ".join(value.split("_"))

