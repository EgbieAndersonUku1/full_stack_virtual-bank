import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from .forms import RegisterForm
from .models import User
from .view_helper import handle_json_post_request, create_json_msg

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
    
    def handle_username(request_body):
       
       email             = request_body.get("email")
       does_email_exists = User.objects.filter(email=email).exists()
    
       return create_json_msg(field_name="email", field_value=email, is_available=does_email_exists)
      
    return handle_json_post_request(request, handle_username)

