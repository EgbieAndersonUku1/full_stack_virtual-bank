from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from bank.services import BankAccountCacheService
from setup.decorators import onboarding_required
from utils.decorators import go_to_staff_page, is_email_verified
from .form import CardRequestForm, CardRequestEmploymentForm

# Create your views here.


basic_information_session_key      = "basic_request"
employment_information_session_key =  "employment_request"



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
     
    context["form"] = form
    return render(request, "card_request/user/card-request-information.html", context) 



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