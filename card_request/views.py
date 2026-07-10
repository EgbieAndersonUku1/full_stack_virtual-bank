from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages


from authentication.view_helper import handle_json_post_request
from setup.decorators import onboarding_required
from utils.decorators import go_to_staff_page, is_email_verified
from .form import CardRequestForm, CardRequestEmploymentForm, CardAgreementForm
from .views_helper import get_card_request_agreement
from .services import CardRequestService
from utils.decorators import is_card_request_application_status_pending


# Create your views here.


basic_information_session_key      = "basic_request"
employment_information_session_key =  "employment_request"



@is_card_request_application_status_pending
@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def card_request_information(request):
    
    form    = CardRequestForm(initial=request.session.get(basic_information_session_key, {}))
    context = {}
    
    if request.method == "POST":
        form = CardRequestForm(request.POST or None)
        
        if form.is_valid():
            
            cleaned_data = form.cleaned_data.copy()
            
            phone_number                 = cleaned_data["phone_number"]
            cleaned_data["phone_number"] = str(phone_number)
            
            request.session[basic_information_session_key] = cleaned_data
            return redirect("card_request_employment")
        else:
            print("not submitted")
            print(form.errors)
     
    context["form"] = form
    return render(request, "card_request/user/card-request-information.html", context) 



@is_card_request_application_status_pending
@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def card_request_employment(request):
    
    form  = CardRequestEmploymentForm(initial=request.session.get(employment_information_session_key, {}))
    
    if request.method == "POST":
        form = CardRequestEmploymentForm(request.POST or None)
            
        if form.is_valid():
           
            request.session[employment_information_session_key] = form.cleaned_data.copy()
            return redirect("card_request_review_and_confirm")
            

    context = {
        "form": form
    }
    return render(request, "card_request/user/card-request-employment.html", context=context)




@is_card_request_application_status_pending
@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def card_request_review_and_confirm(request):
    
    context = {
        "basic_information": request.session.get(basic_information_session_key),
        "employment_information": request.session.get(employment_information_session_key),
    }
    
    return render(request, "card_request/user/review-and-confirm.html", context)



@is_card_request_application_status_pending
@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def card_request_agreement(request):
     
    form = CardAgreementForm()
    
    if request.method == "POST":
        form = CardAgreementForm(request.POST or None)
        
        if form.is_valid():
           
            basic_information = request.session.pop(basic_information_session_key, {})
            employment_information = request.session.pop(employment_information_session_key, {})
            
            CardRequestService.add_card_request_to_database(basic_information=basic_information,
                                                            employment_information=employment_information,
                                                            user=request.user
                                                            )
           
            messages.success(
                request,
                message=(
                    "Your card request has been submitted successfully. "
                    "Your application is now under review. We will contact you once a decision "
                    "has been made."
                )
            )
            return redirect("card_request_information")
          
        
    context = {
        "card_request_agreement": get_card_request_agreement(),
        "form": form,
    }
    return render(request, "card_request/user/agreement/card-request-agreement.html", context)


@csrf_protect
@login_required
def get_card_request_completion_status(request):
    """
    Return the completion status of each stage in the card request process.
    """

    def construct_missing_stage_message(stage_name):
        return (
            f"The {stage_name} is missing from your card request. "
            "Please complete all sections before submitting."
        )

    def build_card_request_completion_status(data):
        
        basic_information      = request.session.get(basic_information_session_key)
        employment_information = request.session.get(employment_information_session_key)

        is_personal_information_complete = basic_information is not None
        is_employment_information_complete = employment_information is not None

        data = {
            "IS_PERSONAL_INFORMATION_COMPLETE": is_personal_information_complete,
            "IS_EMPLOYMENT_INFORMATION_COMPLETE": is_employment_information_complete,
            "STAGE_1_ERROR_MSG": "",
            "STAGE_2_ERROR_MSG": "",
            "SUCCESS": (
                is_personal_information_complete
                and is_employment_information_complete
            ),
           "SUCCESS_MSG": ""
        }

        if not is_personal_information_complete:
            data["STAGE_1_ERROR_MSG"] = construct_missing_stage_message("personal information")

        if not is_employment_information_complete:
            data["STAGE_2_ERROR_MSG"] = construct_missing_stage_message("employment information")
        
        if is_personal_information_complete and is_employment_information_complete:
            data["SUCCESS_MSG"] = (
                    f"Your card request has been submitted successfully. "
                    f"We will review your application and notify you of the outcome shortly."
                )

        return data

    return handle_json_post_request(request, func=build_card_request_completion_status)



@is_card_request_application_status_pending
@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def is_application_pending(request):
    return render(request, "card_request/user/card_request_pending.html")