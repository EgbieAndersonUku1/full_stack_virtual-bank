import logging

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from bank.models import Bank
from .forms import PinConfirmCodeForm
from bank.services.services import get_banks_with_cache_fallback
from setup.services.service import AccountOnboardingService
from .decorators import is_onboarding_steps_completed
from setup.decorators import onboarding_required
from user_profile.forms import UserProfileForm
from utils.decorators import is_email_verified
from utils.safe_cache import get_cache_or_set
from setup.decorators import onboarding_blocked
from utils.decorators import go_to_staff_page
from utils.services.image_processor import  TempImageStorageService
from utils.custom_errors import (MissingUploadedImageFile,
                                 PredifinedBanksCreationError,
                                 MissingBankInformationError
                                 )


logger = logging.Logger(__name__)

# Create your views here.

cache_key = settings.TEMP_PROFILE_IMAGE_SESSION_KEY



@csrf_protect
@is_email_verified
@login_required
def upload_profile_picture(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    context = {
        "SUCCESSFUL": False,
        "MESSAGE": "",
        "ERROR_MSG": "",
        "EXTRA_INFO": {}
    }

    try:
        image = request.FILES.get("image")

        if not image:
            raise MissingUploadedImageFile(_("No image provided"))

        temp_dir = TempImageStorageService.store_temp_image(image, request, cache_key)

        context["SUCCESSFUL"] = True
        context["MESSAGE"]    = "Successfully uploaded image"
        context["EXTRA_INFO"] = {"temp_url": temp_dir.temp_url, "temp_dir": temp_dir.temp_path}

    except Exception as e:
        context["ERROR_MSG"] = str(e)

    return JsonResponse(context)


@go_to_staff_page
@onboarding_blocked
@is_email_verified
@login_required
def bank_setup_welecome(request):
    return render(request, "bank/setup/welcome.html")


@go_to_staff_page
@onboarding_blocked
@is_email_verified
@login_required
def bank_setup_bank_choices(request):

    banks = banks = get_cache_or_set(key=settings.BANK_CACHE_KEY,
                                    value_or_func=lambda: Bank.objects.seeded(),
                                    ttl=settings.BANK_CACHE_TTL
                                    )


    bank_id = request.POST.get("chosen_bank")

    if bank_id:
        request.session["bank_id"]    = bank_id
        request.session["next_step"]  = "choose_pin"
        return redirect("choose_pin")

    context = {
        "banks": banks
    }
    return render(request, "bank/setup/bank-choices.html", context=context)


@go_to_staff_page
@onboarding_blocked
@is_email_verified
@login_required
def bank_setup_pin(request):
    form = PinConfirmCodeForm()

    if request.method == "POST":
        form = PinConfirmCodeForm(request.POST or None)
        if form.is_valid():

            request.session["pin"] = form.cleaned_data.get("pin")
            request.session["next_step"]  = "create_profile"
            return redirect("create_profile")

    context = {
        "form": form,
    }
    return render(request, "bank/setup/bank-pin-setup.html", context=context)


@onboarding_blocked
@is_email_verified
@login_required
def bank_setup_create_profile(request):

    profile_data = request.session.get("profile_draft", {})

    form = UserProfileForm(initial=profile_data)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES)

        if form.is_valid():

            data                   = form.cleaned_data
            cleaned_middle_name    = data["middle_name"]
            cleaned_address_line_2 = data["address_line_2"]
            profile_pic            = request.session.get(cache_key, None)


            request.session["profile_draft"] = {
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "gender": data["gender"],
                "bio": data["bio"],
                "phone_number": str(data["phone_number"]) if data["phone_number"] else None,
                "city": data["city"],
                "address_line_1": data["address_line_1"],
                "postcode": data["postcode"],
                "country": data["country"],
            }

            # Only store middle_name, address line 2 if a value was provided.
            # The profile model already handles missing values
            if cleaned_middle_name:
                request.session["profile_draft"]["middle_name"] = cleaned_middle_name

            if cleaned_address_line_2:
                request.session["profile_draft"]["address_line_2"] = cleaned_address_line_2

            if profile_pic is not None:
                request.session["profile_draft"]["profile_pic"] = profile_pic

            request.session["next_step"]  = "bank_confirmation"
            return redirect("bank_confirmation")

    context = {
        "form": form,
    }

    return  render(request, "bank/setup/bank-create_profile.html", context=context)



@go_to_staff_page
@onboarding_blocked
@is_email_verified
@login_required
def bank_setup_final_confirmation(request):

    bank_id = request.session.get("bank_id")

    context  = {}

    if not bank_id:
        messages.info(request, "You haven't chosen a bank. Please select a bank")
        return redirect("choose_bank")


    banks = get_banks_with_cache_fallback(key=settings.BANK_CACHE_KEY)

    if banks is None:
        raise PredifinedBanksCreationError(_("The predefined banks is missing"))

    context["chosen_bank"] = banks.filter(pk=int(bank_id)).first()
    return  render(request, "bank/setup/bank-completion.html", context=context)


@go_to_staff_page
@onboarding_blocked
@is_onboarding_steps_completed
@is_email_verified
@login_required
def create_bank_account(request):

    bank_id      = request.session.get("bank_id", None)
    profile_data = request.session.get("profile_draft", {})
    banks        = get_banks_with_cache_fallback(key=settings.BANK_CACHE_KEY)

    if banks is None:
        raise PredifinedBanksCreationError(_("The predefined banks is missing"))

    bank = banks.filter(pk=bank_id).first()

    if bank is None:
        raise MissingBankInformationError(_("The bank couldn't be found"))

    resp = AccountOnboardingService.complete_onboarding(user=request.user,
                                                 bank=bank,
                                                 profile_data=profile_data,
                                                 pin=request.session.get("pin", None),
                                                 )

    request.session.pop("bank_id")
    request.session.pop("profile_draft")

    if hasattr(request.session, cache_key):
        request.session.pop(cache_key)

    if resp:
        messages.success(request,
                "Your account has been successfully created. We've sent a welcome email with your account details."
                )

        return redirect("dashboard")

    messages.error(request, "Something went wrong and the profile wasn't created. Please try again.")
    return redirect("setup-welcome")

