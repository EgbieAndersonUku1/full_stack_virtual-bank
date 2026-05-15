from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from human_seconds.converter import SecondsToTime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db import transaction
from human_seconds.converter import SecondsToTime
from django.conf import settings


from .forms import RegisterForm, LoginForm, EmailConfirmCodeForm
from .models import User, Verification, VerificationStatus
from .view_helper import handle_json_post_request, create_json_msg
from utils.security.generator import generate_secure_code
from utils.send_email import send_confirmation_email_with_async
from utils.decorators import go_to_staff_page

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
            
            return redirect("login_user")
        
    
    context = {
        "form": form,
    }

    return render(request, "authentication/bank/authentication/register.html", context=context)


def logout_user(request):
    logout(request)
    return redirect("bank_home")


@csrf_protect
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
    
    form             = EmailConfirmCodeForm()
    restrict_account = False
    
    verification = Verification.get_by_user_and_type(request.user, Verification.VerificationType.EMAIL_VERIFICATION)

    if verification:
        restrict_account = verification.is_blocked
   

    if request.method == "POST":
     
        form = EmailConfirmCodeForm(request.POST or None)
        error_msg = _("The code entered is invalid!")

        if form.is_valid():

            code         = form.cleaned_data.get("code")
            verification = Verification.get_by_user_and_code(user=request.user, verification_code=code)

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
def request_email_verification_code(request):
    
    user        = request.user
    secure_code = generate_secure_code()
    status      = None

    context  = {
        "form": EmailConfirmCodeForm(),
        "resend": True,
    }

    with transaction.atomic():
    
        # acquires a row-level lock to ensure safe concurrent updates which prevents race conditions
        verification, created = Verification.objects.select_for_update().get_or_create(
            user=user,
            verification_type=Verification.VerificationType.EMAIL_VERIFICATION,
            
        )

        if not created:
            status = verification.get_status()
       
    if status is None:
        messages.error(
                request,
                _("Something went wrong. Please request a new verification code.")
            )
        
    match status:

        case VerificationStatus.USED:
            return redirect("dashboard")
        
        case VerificationStatus.LOCKED:
            context["restrict_account"] = True
      
        case VerificationStatus.COOLDOWN:
            wait_time = SecondsToTime(seconds=verification.cooldown_seconds_left).format_to_human_readable()
            messages.info(request, _(f"You need to wait {wait_time} before request a new code"))

        case VerificationStatus.RESENT:
            messages.success( request,
                             _("We've sent a new verification code to your email.")
                        )

            verification.increment_resend(commit=False)
            verification.verification_code = secure_code
            verification.set_expiry(minutes=settings.DEFAULT_CODE_EXPIRY_IN_MINUTES)
            verification.save()

            send_confirmation_email_with_async(username=user.username,
                                                email=user.email, 
                                                subject="New Verification Code Request: Confirm Your Email Address", 
                                                verification_code=secure_code,
                                                expiry_time=SecondsToTime(verification.get_expiry_seconds()).format_to_human_readable())
            
    return render(request, "authentication/bank/authentication/verify_code.html", context=context)