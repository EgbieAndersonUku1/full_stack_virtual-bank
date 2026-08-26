from decimal import Decimal
from enum import StrEnum
from typing import Literal, TypedDict

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bank.models import BankAccount, LedgerEntry
from bank.services.bank_services import BankAccountCacheService
from utils.custom_errors import MissingAccountError
from utils.security.generator import generate_secure_code as generate_reference
from utils.validators.validators import validate_user

User = get_user_model()


class AccountType(StrEnum):
    CURRENT_ACCOUNT = "current_account"
    SAVING_ACCOUNT = "saving_account"
    BANK_CARD = "bank_card"


Accounts = Literal[AccountType.CURRENT_ACCOUNT, AccountType.SAVING_ACCOUNT]


class FundingResponse(TypedDict):
    account: BankAccount
    ledger_entry: LedgerEntry


class FundingService:
    RISK_THRESHOLD = Decimal("10000.00")

    @classmethod
    def _get_bank_account_or_raise(
        cls, user: User, destination: Accounts
    ) -> BankAccount:
        """
        Retrieve the funding destination for a user.

        The destination may be the user's current account, savings account,
        or default bank card. If the requested destination cannot be found,
        a ``MissingAccountError`` is raised.

        Args:
            user (User): The user whose funding destination should be retrieved.
            destination (AccountType): The type of destination to retrieve,
                such as a current account, savings account, or bank card.

        Returns:
            BankAccount: The requested funding destination.

        Raises:
            MissingAccountError: If the requested funding destination does not
                exist for the user.
            ValueError: If an unsupported destination type is supplied.
        """

        if destination == AccountType.CURRENT_ACCOUNT:
            account = BankAccountCacheService.get_current_account(user)

        elif destination == AccountType.SAVING_ACCOUNT:
            account = BankAccountCacheService.get_saving_account(user)

        else:
            raise ValueError(f"Unsupported destination: {destination}")

        if not account:
            raise MissingAccountError(
                _("The requested funding destination could not be found.")
            )

        return account

    @classmethod
    def _add_funds_to_destination(
        cls, amount: Decimal, user: User, account_to_fund: str
    ) -> FundingResponse:

        validate_user(user)
        account = cls._get_bank_account_or_raise(user=user, destination=account_to_fund)

        with transaction.atomic():

            opening_balance = account.balance

            ledger_entry = LedgerEntry(
                reference=f"TX_{generate_reference(code_length=35)}",
                transaction_type=LedgerEntry.TransactionType.ADD_FUNDS,
                source=LedgerEntry.Source.EXTERNAL,
                opening_balance=opening_balance,
                amount=amount,
                currency="GBP",  # for now use GBP, later the currency will come from the account when implemented
                description=f"The user {user} funded their account with the amount {amount}",
                movement=LedgerEntry.Movement.CREDIT,
                user=user,
                account=account,
            )

            if amount >= cls.RISK_THRESHOLD:
                ledger_entry.risk_flag = True
                ledger_entry.risk_reason = f"User {user} funded the account with an amount that exceeded the risk threshold."

                ledger_entry.status = LedgerEntry.Status.PENDING
                ledger_entry.review_required = True
            else:

                # Only credit the amount if it hasn't been flagged
                account.credit(amount)

                # user's bank account is pending until a successful first time credit is made
                if account.status == BankAccount.Status.PENDING:
                    account.status = BankAccount.Status.ACTIVE

                account.save()
                BankAccountCacheService.set(user)

                ledger_entry.status = LedgerEntry.Status.COMPLETED
                ledger_entry.completed_on = timezone.now()

            ledger_entry.closing_balance = account.balance
            ledger_entry.save()

            resp: FundingResponse = {
                "account": account,
                "ledger_entry": ledger_entry,
            }
            return resp

    @classmethod
    def add_funds_to_saving_account(
        cls, amount: Decimal, user: User
    ) -> FundingResponse:
        """
        Add funds to the user's saving bank account.

        The supplied amount is credited to the user's current account and a
        corresponding ledger entry is created. If the amount being funded meets or
        exceeds the configured risk threshold, the transaction is flagged for
        review and the account balance is not immediately increased.

        Amount validation is handled by the model layer.

        Args:
            amount (Decimal): The positive amount to add to the user's current account.
            user (User): The user whose current account will be funded.

        Returns:
            FundingResponse: A dictionary containing the current bank account and
            the corresponding ledger entry.

        Note:
            ``amount`` should be converted to ``Decimal`` before calling this method.

             In particular, avoid converting through a float when constructing a ``Decimal``.

             For example:

            >>> from decimal import Decimal
            >>> amount = Decimal("200.00")
            >>> FundingService.add_funds_to_saving_account(amount, user)
                {
                    "account": saving_account,
                    "ledger_entry": ledger_entry,
                }

        """
        return cls._add_funds_to_destination(
            amount=amount, user=user, account_to_fund=AccountType.SAVING_ACCOUNT
        )

    @classmethod
    def add_funds_to_current_account(
        cls, amount: Decimal, user: User
    ) -> FundingResponse:
        """
        Add funds to the user's current bank account.

        The supplied amount is credited to the user's current account and a
        corresponding ledger entry is created. If the amount being funded meets or
        exceeds the configured risk threshold, the transaction is flagged for
        review and the account balance is not immediately increased.

        Amount validation is handled by the model layer.

        Args:
            amount (Decimal): The positive amount to add to the user's current
                account.
            user (User): The user whose current account will be funded.

        Returns:
            FundingResponse: A dictionary containing the current bank account and
            the corresponding ledger entry.

        Note:
            ``amount`` should be converted to ``Decimal`` before calling this method.

            In particular, avoid converting through a float when constructing a ``Decimal``.

            For example:

                >>> from decimal import Decimal
                >>> amount = Decimal("200.00")
                >>> FundingService.add_funds_to_current_account(amount, user)
                {
                    "account": current_account,
                    "ledger_entry": ledger_entry,
                }

        """
        return cls._add_funds_to_destination(
            amount=amount, user=user, account_to_fund=AccountType.CURRENT_ACCOUNT
        )

