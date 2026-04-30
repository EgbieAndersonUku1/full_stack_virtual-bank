from functools import wraps
from django.shortcuts import redirect


def is_email_verified(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            if request.user and not request.user.is_user_email_verified():
                return redirect("confirm_registration_code")
            return func(request, *args, **kwargs)
        except AttributeError:
             return func(request, *args, **kwargs)
    return wrapper


