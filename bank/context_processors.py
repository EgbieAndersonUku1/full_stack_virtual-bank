
from bank.services.ledger_services import LedgerEntryCache
from utils.custom_errors import ProfileNotFoundError
from bank.services.bank_services import BankAccountCacheService
from utils.formatter import format_currency


def bank_details(request):

    if not request.user.is_authenticated:
        return {
            "bank_balance": None
        }

    try:
        user = request.user
        bank_account = BankAccountCacheService.get_current_account(user)
        pending_amount = LedgerEntryCache.get_pending_amount_or_refresh(user)

        if pending_amount:
            pending_amount = format_currency(pending_amount)

        return {
            "bank_balance": bank_account.balance if bank_account else 0.00,
            "pending_amount": pending_amount
        }
    except ProfileNotFoundError:
        return {}
