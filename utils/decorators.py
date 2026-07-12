import logging
from functools import wraps
from django.shortcuts import redirect
from card_request.services import construct_card_application_session_key
from utils.safe_cache import get_cache_or_set
from card_request.models import CardRequestApplication


logger = logging.getLogger("application")


def is_email_verified(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            if request.user and not request.user.is_superuser and not request.user.is_user_email_verified():
                return redirect("confirm_registration_code")
            return func(request, *args, **kwargs)
        except AttributeError:
             return func(request, *args, **kwargs)
    return wrapper



def has_superuser_permissions(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            if request.user and not request.user.is_superuser:
                return redirect("dashboard")
            return func(request, *args, **kwargs)
        except AttributeError:
             return func(request, *args, **kwargs)
    return wrapper



def go_to_staff_page(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            if request.user and (request.user.is_superuser or request.user.is_staff):
                return redirect("employee_services")
            return func(request, *args, **kwargs)
        except AttributeError:
             return func(request, *args, **kwargs)
    return wrapper


def is_card_request_application_status_pending(func):
    
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            user = request.user
            if user:
                cache_key = construct_card_application_session_key(user.username)
                
                status = get_cache_or_set(key=cache_key,
                                          value_or_func=lambda: CardRequestApplication.get_user_applications(user=user,
                                                                                                             status=CardRequestApplication.Status.PENDING
                                                                                                             ).values_list("status", 
                                                                                                                           flat=True
                                                                                                                           ).first()
                                              )
              
               
                logger.debug("Card request status=%s pending=%s", status, status == CardRequestApplication.Status.PENDING)
                
                if status == CardRequestApplication.Status.PENDING and request.resolver_match.url_name != "application_status":
                    return redirect("application_status")

                
                if status is None and request.resolver_match.url_name == "application_status":
                    return redirect("card_request_information")
    
                return func(request, *args, **kwargs)
        except AttributeError:
            return func(request, *args, **kwargs)
            
    
    return wrapper