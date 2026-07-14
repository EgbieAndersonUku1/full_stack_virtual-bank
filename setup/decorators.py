from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist


from functools import wraps



def is_onboarding_steps_completed(func):

    @wraps(func)
    def wrapper(request, *args, **kwargs):

        if not request.session.get("bank_id", None):
            messages.info(request, "You haven't chosen a bank. Please select a bank.")
            return redirect("choose_bank")

        if not request.session.get("profile_draft", {}):
            messages.info(request,"You haven't created a profile. Please create a profile before continuing.")
            return redirect("create_profile")

        if not request.session.get("pin", None):
            messages.info(request, "You haven't created a PIN. Please create a PIN for transactions.")
            return redirect("choose_pin")

        return func(request, *args, **kwargs)

    return wrapper


def onboarding_required(func):

    @wraps(func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login_user")

        if request.user.is_staff or request.user.is_superuser or request.user.is_admin:
            return redirect("employee_services")

        try:
            request.user.profile
            has_profile = True
        except ObjectDoesNotExist:
            has_profile = False

        if not has_profile:
            next_step = request.session.get("next_step", "setup_welcome")

            return redirect(next_step)

        return func(request, *args, **kwargs)

    return wrapper



def onboarding_blocked(func):

    @wraps(func)
    def wrapper(request, *args, **kwargs):

        if hasattr(request.user, "profile"):
            return redirect("dashboard")

        return func(request, *args, **kwargs)

    return wrapper
