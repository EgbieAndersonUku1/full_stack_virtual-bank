from utils.custom_errors import ProfileNotFoundError
from bank.services.services import BankAccountCacheService


def bank_details(request):

    if not request.user.is_authenticated:
        return {
            "bank_balance": None
        }

    try:
        bank_account = BankAccountCacheService.get_current_account(request.user)

        return {
            "bank_balance": bank_account.balance if bank_account else 0.00,
        }
    except ProfileNotFoundError:
        return {}
