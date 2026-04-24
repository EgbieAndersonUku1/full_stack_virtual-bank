from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import RegisterForm

# Create your views here.


def login_user(request):

    # pin setup
    # bank setup
    
    return render(request, "authentication/bank/authentication/login.html")


def register_user(request):

    form = RegisterForm()

    if request.method == "POST":
        form = RegisterForm(request.POST or None)

        if form.is_valid():
            user = form.save(commit=False)
            print("The form has been submitted") # for testing
            return redirect("login_user")
        
    
    context = {
        "form": form,
    }

    return render(request, "authentication/bank/authentication/register.html", context=context)