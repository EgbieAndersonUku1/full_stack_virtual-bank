
from typing import Any
from django.db.models import QuerySet

from .models import BankAccount



def get_account_context(bank_accounts: QuerySet[BankAccount]) -> dict[str, Any]:
    """
    Return a dictionary of account-related context for templates.

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

    accounts          = list(bank_accounts[:2])
    number_of_accounts = len(accounts)

    return {
        "number_of_accounts": number_of_accounts,
        "current_account": accounts[0] if  number_of_accounts > 0 else None,
        "saving_account": accounts[1] if  number_of_accounts > 1 else None,
    }