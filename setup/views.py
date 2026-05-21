
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.conf import settings


from bank.models import Bank
from user_profile.forms import UserProfileForm
from utils.decorators import is_email_verified
from .forms import PinConfirmCodeForm
from utils.safe_cache import get_cache_or_set
from utils.services.image_processor import  TempImageStorageService
from utils.custom_errors import MissingUploadedImageFile



# Create your views here.

@is_email_verified
@login_required
def bank_setup_welecome(request):
    return render(request, "bank/setup/welcome.html")



@is_email_verified
@login_required
def bank_setup_pin(request):
    form = PinConfirmCodeForm()

    if request.method == "POST":
        form = PinConfirmCodeForm(request.POST or None)
        if form.is_valid():
            request.session["code"] = form.cleaned_data.get("code")
            return redirect("create_profile")
      
    context = {
        "form": form,
    }
    return render(request, "bank/setup/bank-pin-setup.html", context=context)



@is_email_verified
@login_required
def bank_setup_bank_choices(request):

    banks = banks = get_cache_or_set(key=settings.BANK_CACHE_KEY, 
                                    value_or_func=lambda: Bank.get_all_banks(), 
                                    ttl=settings.BANK_CACHE_TTL
                                    )
    
    bank_id = request.POST.get("chosen_bank")

    if bank_id:
        request.session["bank_id"] = bank_id
        return redirect("choose_pin")
    
    context = {
        "banks": banks
    }
    return render(request, "bank/setup/bank-choices.html", context=context)



@is_email_verified
@login_required
def bank_setup_create_profile(request):
    
    form = UserProfileForm()

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES)

    context = {
        "form": form,
    }

    return  render(request, "bank/setup/bank-create_profile.html", context=context)


@is_email_verified
@login_required
def bank_setup_completion(request):
    return  render(request, "bank/setup/bank-completion.html")



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

        temp_dir = TempImageStorageService.store_temp_image(image, request=request)

        context["SUCCESSFUL"] = True
        context["MESSAGE"]    = "Successfully uploaded image"
        context["EXTRA_INFO"] = {"temp_url": temp_dir.temp_url, "temp_dir": temp_dir.temp_path}

    except Exception as e:
        context["ERROR_MSG"] = str(e)

    return JsonResponse(context)