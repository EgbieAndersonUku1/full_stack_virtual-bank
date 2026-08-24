
from typing import Any
from collections.abc import Iterable

from bank.services.bank_services import BankAccountCacheService

from .models import BankAccount
from utils.formatter import format_currency



def get_account_context(bank_accounts) -> dict[str, Any]:
    """
    Return a dictionary of account-related context for templates.

    Accepts either a BankAccount or an iterable of BankAccount objects.

    The first account is treated as the current account and the second
    account, if present, is treated as the savings account. The returned
    dictionary can be merged directly into a view context using
    ``context.update()``.

    Args:
        bank_accounts: A QuerySet or iterable containing up to two bank
            accounts.

    Returns:
        dict: Context containing the current account, savings account,
        and the expected number of accounts.
    """

    total_account_balances = "N/A"

    if isinstance(bank_accounts, BankAccount):
        accounts = [bank_accounts]
    elif isinstance(bank_accounts, Iterable):
        accounts = list(bank_accounts[:2])
    else:
        accounts = []

    number_of_accounts = len(accounts)

    if number_of_accounts >= 1:
        user = accounts[0].user_profile.user
        total_account_balances = format_currency(BankAccountCacheService.get_total_account_balance(user))

    return {
        "number_of_accounts": number_of_accounts,
        "current_account": accounts[0] if  number_of_accounts > 0 else None,
        "saving_account": accounts[1] if  number_of_accounts > 1 else None,
        "total_account_balances": total_account_balances,
    }
