from bank.services.bank_services import BankAccountCacheService
from bank.services.ledger_services import LedgerEntryCache
from bank.services.transaction_services import UserRecentTransactionsCacheService
from utils.custom_errors import ProfileNotFoundError
from utils.formatter import format_currency


def bank_details(request):

    if not request.user.is_authenticated:
        return {"bank_balance": None}

    try:
        user = request.user
        bank_account = BankAccountCacheService.get_current_account(user)
        pending_amount = LedgerEntryCache.get_pending_amount_or_refresh(user)
        UserRecentTransactionsCacheService.get_or_refresh(user)

        bank_details = {}

        if pending_amount:
            pending_amount = format_currency(pending_amount)

        if bank_account:
            bank_details["bank_balance"]      = bank_account.balance
            bank_details["available_balance"] = bank_account.available_balance
        else:
            bank_details["bank_balance"]           = 0.00
            bank_details["available_balance"] = 0.00


        return {
            "bank_balance": bank_details["bank_balance"],
            "available_balance": bank_details["available_balance"],
            "pending_amount": pending_amount,
        }
    except ProfileNotFoundError:
        return {}
