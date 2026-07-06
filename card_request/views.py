from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

from setup.decorators import onboarding_required
from utils.decorators import go_to_staff_page, is_email_verified
from .form import CardRequestForm, CardRequestEmploymentForm

# Create your views here.




@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def card_request_information(request):
    
    form    = CardRequestForm()
    context = {}
    
    if request.method == "POST":
        form = CardRequestForm(request.POST or None)
        
        if form.is_valid():
    
            request.session["basic_request"] = form.cleaned_data.copy()
            return redirect("card_request_employment")
     
    context["form"] = form
    return render(request, "card_request/user/card-request-information.html", context) 



@onboarding_required
@go_to_staff_page
@is_email_verified
@login_required
def card_request_employment(request):
    form = CardRequestEmploymentForm()
    
    if request.method == "POST":
        form = CardRequestEmploymentForm(request.POST or None)
            
        if form.is_valid():
           
            request.session["employement_request"] = form.cleaned_data.copy()
            return redirect("card_request_review_and_confirm")
            

    context = {
        "form": form
    }
    return render(request, "card_request/user/card-request-employment.html", context=context)




def card_request_review_and_confirm(request):
    return HttpResponse("TODO: Implement review and confirm page.")