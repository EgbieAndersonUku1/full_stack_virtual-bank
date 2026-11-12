import logging
from django.views.decorators.http import require_http_methods

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from human_seconds.converter import SecondsToTime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site



from .forms import ForgottenPasswordForm, RegisterForm, LoginForm, EmailConfirmCodeForm, ResetPasswordForm
from .models import User, Verification, VerificationStatus
from .view_helper import handle_json_post_request, create_json_msg
from utils.security.generator import generate_secure_code
from utils.send_email import send_confirmation_email_with_async, send_forgotten_password_link_with_async
from utils.decorators import go_to_staff_page

logger = logging.getLogger(__name__)

# Create your views here.


def login_user(request):

    form = LoginForm()

    if request.method == "POST":
        form = LoginForm(request.POST or None)

        if form.is_valid():

            cleaned_data = form.cleaned_data
            email         = cleaned_data.get("email").lower()
            password      = cleaned_data.get("password")
            user          = authenticate(request, email=email, password=password)

            if user is not None:

               login(request, user)

               if not user.is_user_email_verified():
                   return redirect("confirm_registration_code")
               return redirect("dashboard")


        messages.error(request, _("The email and password is invalid"))

    context = {
        "form": form
    }
    return render(request, "authentication/bank/authentication/login.html", context=context)


@require_http_methods(["GET", "POST"])
def register_user(request):

    form = RegisterForm()

    if request.method == "POST":
        form = RegisterForm(request.POST or None)

        if form.is_valid():

            user        = form.save()
            secure_code = generate_secure_code()

            verification = Verification(user=user,
                                        verification_code=secure_code,
                                        description="Verify email for registration code"
                                        )
            verification.set_expiry(minutes=settings.DEFAULT_CODE_EXPIRY_IN_MINUTES)
            verification.save()

            send_confirmation_email_with_async(username=user.username,
                                                email=user.email,
                                                subject="Confirm email address",
                                                verification_code=secure_code,
                                                expiry_time=SecondsToTime(verification.get_expiry_seconds()).format_to_human_readable())

            messages.info(request, _("We've sent a confirmation email. Please check your inbox to continue."))

            return redirect(reverse("authentication_login_user"))


    context = {
        "form": form,
    }

    return render(request, "authentication/bank/authentication/register.html", context=context)


def logout_user(request):
    logout(request)
    return redirect("bank_home")


@csrf_protect
@require_http_methods(["POST"])
def does_username_exists(request):
    """
    Handle a POST request to check if a username already exists.

    Expects a JSON payload containing a "username" field. The function
    queries the User model to determine whether the provided username
    is already in use.

    Returns:
        JsonResponse: A JSON response containing:
            - field_name (str): The name of the field ("username")
            - field_value (str): The submitted username
            - is_available (bool): True if the username exists, False otherwise
            - msg (str): A message describing the result

    Notes:
        - This view is protected against CSRF attacks.
        - Delegates request handling to `handle_json_post_request`.
    """

    def handle_username(request_body):

       username             = request_body.get("username")
       does_username_exists = User.objects.filter(username=username).exists()

       return  create_json_msg(field_name="username", field_value=username, is_available=does_username_exists)

    return handle_json_post_request(request, handle_username)



@csrf_protect
@require_http_methods(["POST"])
def does_email_exists(request):
    """
    Handle a POST request to check if an email already exists.

    Expects a JSON payload containing an "email" field. The function
    queries the User model to determine whether the provided email
    is already registered.

    Returns:
        JsonResponse: A JSON response containing:
            - field_name (str): The name of the field ("email")
            - field_value (str): The submitted email
            - is_available (bool): True if the email exists, False otherwise
            - msg (str): A message describing the result

    Notes:
        - This view is protected against CSRF attacks.
        - Delegates request handling to `handle_json_post_request`.
    """

    def handle_email(request_body):

       email             = request_body.get("email")
       does_email_exists = User.objects.filter(email=email).exists()

       return create_json_msg(field_name="email", field_value=email, is_available=does_email_exists)

    return handle_json_post_request(request, handle_email)



def terms_and_conditions(request):
    return render(request, "terms_and_conditions.html")


@go_to_staff_page
@login_required
def verify_registration_code(request):

    if request.user.is_user_email_verified():
        messages.info(request, "You have already verified your verification code")
        return redirect("dashboard")

    form  = EmailConfirmCodeForm()

    restrict_account = (
            Verification.objects.filter(
                user=request.user,
                verification_type=Verification.VerificationType.EMAIL_VERIFICATION,
            )
            .values_list("status", flat=True)
            .first()
        ) == Verification.Status.BLOCKED

    if request.method == "POST":

        form                    = EmailConfirmCodeForm(request.POST or None)
        error_msg               = _("The code entered is invalid!")
        verification_successful = False

        if form.is_valid():

            with transaction.atomic():

                cleaned_code = form.cleaned_data.get("code")
                verification = Verification.get_by_user_and_code(user=request.user,
                                                                 for_update=True,
                                                                 verification_code=cleaned_code)

                if verification:

                    restrict_account = verification.is_blocked

                    if verification.is_code_expired:
                        error_msg    = _("Your verification code has expired. Please request a new one.")
                        verification.mark_as_expired()
                    elif verification.is_used:
                        error_msg = _("You have already used the code")
                    else:
                        request.user.mark_email_as_verified()
                        verification.mark_as_used()
                        verification_successful = True

            if verification_successful:
                messages.success(request, _("You have successfully verified your code. Next we begin your onboarding"))
                return redirect("setup_welcome")

        messages.error(request, error_msg)

    context = {
        "form": form,
        "resend": False,
        "restrict_account": restrict_account,
    }

    return render(request, "authentication/bank/authentication/verify_code.html", context=context)



@login_required
@require_http_methods(["GET", "POST"])
def request_email_verification_code(request):

    user = request.user
    email_scheduled = False
    message_type = None
    message = None

    context = {
        "form": EmailConfirmCodeForm(),
        "resend": True,
    }

    if request.method == "POST":

        with transaction.atomic():

            verification = Verification.get_by_user_and_type(user=request.user,
                                                             verification_type=Verification.VerificationType.EMAIL_VERIFICATION
                                                             )

            status = verification.get_status()

            if status is None:
                logger.error(
                    "Verification.get_status() returned None unexpectedly. "
                    "User ID: %s, Verification ID: %s",
                    user.pk,
                    verification.pk,
                )
                message_type = "error"
                message = _("Something went wrong. Please request a new verification code.")

            else:

                match status:

                    case VerificationStatus.USED:
                        return redirect("dashboard")

                    case VerificationStatus.LOCKED:
                        context["restrict_account"] = True

                    case VerificationStatus.COOLDOWN:
                        wait_time = SecondsToTime(
                            seconds=verification.cooldown_seconds_left
                        ).format_to_human_readable()

                        message_type = "info"
                        message = _(f"You need to wait {wait_time} before requesting a new code.")

                    case VerificationStatus.CAN_SEND:
                        secure_code = generate_secure_code()

                        verification.increment_resend(commit=False)
                        verification.verification_code = secure_code
                        verification.set_expiry(
                            minutes=settings.DEFAULT_CODE_EXPIRY_IN_MINUTES
                        )
                        verification.save()

                        expiry_time = SecondsToTime(
                            verification.get_expiry_seconds()
                        ).format_to_human_readable()

                        transaction.on_commit(
                            lambda: send_confirmation_email_with_async(
                                username=user.username,
                                email=user.email,
                                subject="New Verification Code Request: Confirm Your Email Address",
                                verification_code=secure_code,
                                expiry_time=expiry_time,
                            )
                        )

                        email_scheduled = True

                    case _:
                        logger.error(
                            "Unexpected verification status returned. "
                            "User ID: %s, Verification ID: %s, Status: %s",
                            user.pk,
                            verification.pk,
                            status,
                        )
                        message_type = "error"
                        message = _("Something went wrong and the email wasn't sent.")

        # Display messages after the transaction has completed.
        if email_scheduled:
            messages.success(
                request,
                _("We've requested a new verification code for you. Please check your inbox shortly.")
            )

        elif message_type == "error":
            messages.error(request, message)

        elif message_type == "info":
            messages.info(request, message)

    return render(
        request,
        "authentication/bank/authentication/verify_code.html",
        context=context,
    )


@require_http_methods(["GET", "POST"])
def forgotten_password(request):

    form  = ForgottenPasswordForm()

    if request.method == "POST":

        form = ForgottenPasswordForm(request.POST)

        if form.is_valid():
            cleaned_email = form.cleaned_data["email"].lower()

            send_forgotten_password_link_with_async(
                email=cleaned_email,
                subject="Reset your password link",
                domain=get_current_site(request).domain,
                use_https=request.is_secure(),

            )

            messages.success(request,
                "If an account exists with this email address, "
                "we'll send you a password reset link."
            )

    context = {
        "form": form,
    }

    return render(
        request,
        "authentication/bank/passwords/forgotten_password.html",
        context=context
    )



def reset_password(request, username: str, token: str):
    context = {"form": ResetPasswordForm()}
    return render(request,
                  "authentication/bank/passwords/reset_password.html",
                  context=context)
