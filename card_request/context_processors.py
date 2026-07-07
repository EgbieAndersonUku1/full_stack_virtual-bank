from bank.utils import get_account_context
from utils.custom_errors import ProfileNotFoundError
from bank.services import BankAccountCacheService


def display_bank_details_on_card(request):
    
    if not request.user.is_authenticated:
        return {
             "current_account": None
        }

    try:
        
        context = {}
        bank_account = BankAccountCacheService.get_current_account(request.user)

        # print(bank_account)
        
        context.update(get_account_context(bank_account))
        return context
    
    except ProfileNotFoundError:
        return {}
    



def display_application_summary_details(request):
    
    if not request.user.is_authenticated:
        return {}

    try:
        
        context = {
            "basic_information" : request.session.get("basic_request")
        }
       
        return context
    
    except:
        return {}