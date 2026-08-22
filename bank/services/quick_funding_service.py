"""
Application services for handling quick account funding.

This module provides the application-level workflow for funding a user's
bank account through the quick-funding functionality.

The quick-funding service is responsible for:

- Validating the user's PIN before initiating a funding request.
- Converting the supplied amount to a ``Decimal``.
- Selecting the appropriate account funding service.
- Delegating the actual financial transaction to the relevant funding service.
- Returning a consistent response describing the outcome of the request.

The underlying financial transaction, including ledger creation, account
balance updates, risk checks, and database transaction management, is handled
by the appropriate funding service.

This separation keeps API-facing application logic separate from the core
financial transaction logic.

Note:
    This service is intentionally different from ``FundingService``.

    ``FundingService`` is responsible for performing the actual financial
    transaction and does not perform PIN validation. It can therefore be used
    internally when PIN validation has already been handled or is not required.

    The quick-funding service is intended for API requests where the user's
    PIN must be verified before any funds are credited to the account.

    Use the quick-funding service when a PIN is required. Use ``FundingService``
    directly when PIN validation is not part of the operation.
"""


from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Callable, TypedDict, Literal
from django.contrib.auth import get_user_model

from bank.services.funding_service import FundingService, FundingResponse
from setup.models import Pin


User = get_user_model()

AccountType = Literal["current_account", "saving_account"]



class Action(StrEnum):
    """
    Defines the possible outcomes of a quick funding request which
    is readable for the frontend.
    """

    ACCOUNT_CREDITED       = "Account Credited"
    FUNDING_PENDING_REVIEW = "Funding Pending Review"
    INVALID_PIN            = "Invalid Pin"
    INVALID_AMOUNT         = "Invalid amount"
    INTERNAL_ERROR         = "Internal Error"



class QuickFundResponse(TypedDict):
    SUCCESS: bool
    MSG: str
    ACTION: str
    AMOUNT: Decimal
    BALANCE: Decimal




class QuickFundingService:
    """
    Application service for handling user-initiated quick funding requests.

    This service coordinates the steps required to fund a user's bank account
    through the quick-funding workflow. It acts as an application-level layer
    between the API/view and the underlying ``FundingService``.

    Responsibilities include:

    - Retrieving and validating the user's PIN.
    - Converting the supplied funding amount to ``Decimal``.
    - Selecting the appropriate account funding operation.
    - Delegating the actual financial transaction to ``FundingService``.
    - Interpreting the resulting ledger entry.
    - Returning a consistent response suitable for the API layer.

    The service does not directly modify account balances or create ledger
    entries. Those financial operations are delegated to ``FundingService``.

    Use this service when a funding request originates from an API workflow
    where the user's PIN must be verified before funds can be credited.

    ``FundingService`` should be used directly when PIN validation has already
    been handled elsewhere or is not required.
    """

    @classmethod
    def _convert_amount_to_decimal(cls, amount: int | float) -> Decimal | None:
        """
        Convert a numeric funding amount to ``Decimal``.

        The amount is first converted to a string before being passed to
        ``Decimal`` to avoid floating-point precision issues.

        Args:
            amount: The amount supplied by the user.

        Returns:
            A ``Decimal`` representation of the amount, or ``None``
            if the amount cannot be converted to ``Decimal``.
        """
        try:
            return Decimal(str(amount))
        except InvalidOperation:
            return None

    @classmethod
    def _get_funding_method(cls, account_to_fund: str = "current_account") -> Callable[[Decimal, User], FundingResponse]:
        """
        Return the funding service method for the requested account type.

        Args:
            account_to_fund: The type of account to fund.

        Returns:
            The funding service method responsible for funding the requested account type.

        Raises:
            KeyError: If the supplied account type is not supported.
        """
        return {
            "current_account": FundingService.add_funds_to_current_account,
        }[account_to_fund]

    @classmethod
    def _fund_account(cls, user_pin: str, amount: int | float,
                       user: User,
                       account_type: AccountType = "current_account"
                       ) -> QuickFundResponse:

        """
        Process a quick funding request for a user's bank account.

        The user's PIN is verified before the funding operation is performed.
        If the PIN is valid, the supplied amount is converted to ``Decimal``
        and passed to the appropriate funding service.

        Args:
            user_pin: The PIN supplied by the user for authorization.
            amount: The amount to fund the account with.
            user: The user whose account is being funded.
            account_type: The type of account to fund.

        Returns:
            A ``QuickFundResponse`` containing a success status and a message
            describing the outcome of the funding request.

        Note:
            If the funding amount exceeds the configured risk threshold, the
            funding request may be placed into a pending review state rather
            than immediately crediting the account.
        """

        data: QuickFundResponse = {
            "SUCCESS": False,
            "MSG": "",
            "ACTION": "",
            "AMOUNT": Decimal("0.00"),
            "BALANCE": Decimal("0.00")
        }

        # PIN verification must occur before delegating to the financial service.
        pin = Pin.get_pin_by_user(user=user)

        if not pin:
            data["MSG"] = (
                    "Something went wrong and the user associated with pin wasn't found. "
                    "Try again later."
                )
            data["ACTION"] = Action.INTERNAL_ERROR
            return data

        is_valid = pin.verify_pin(user_pin)

        if not is_valid:
            data["MSG"]   = "The pin entered is invalid"
            data["ACTION"] = Action.INVALID_PIN
            return data

        decimal_amount = cls._convert_amount_to_decimal(amount)

        if decimal_amount is None:
            data["MSG"] = (
                    f"The amount entered is invalid. Expected a float or int, "
                    f"but got type {type(amount).__name__}."
                )

            data["ACTION"] = Action.INVALID_AMOUNT
            return data

        func = cls._get_funding_method(account_to_fund=account_type)
        resp = func(amount=decimal_amount, user=user)

        data["SUCCESS"] = True
        ledger_entry    = resp["ledger_entry"]
        data["BALANCE"] = ledger_entry.closing_balance

        if ledger_entry.risk_flag:
            data["ACTION"]  = Action.FUNDING_PENDING_REVIEW
            data["MSG"]     = (
                    "Your funding request is pending review because the amount exceeds "
                    "the risk threshold."
            )
            return data

        data["MSG"]    = f"Your account has been successfully credited with {ledger_entry.amount}."
        data["AMOUNT"] = ledger_entry.amount
        data["ACTION"] = Action.ACCOUNT_CREDITED

        return data

    @classmethod
    def quick_fund_current_account(cls, pin: str, amount: int | float, user: User) -> QuickFundResponse:
        """
        Quickly fund the user's current account after PIN verification.

        Args:
            pin: The user's PIN used to authorize the funding request.
            amount: The amount to add to the current account.
            user: The user whose current account will be funded.

        Returns:
            A ``QuickFundResponse`` describing the result of the funding
            request.
        """
        return cls._fund_account(user_pin=pin, amount=amount, user=user)

    @classmethod
    def quick_fund_saving_account(cls, pin: str, amount: int | float, user: User) -> QuickFundResponse:
        """
        Quickly fund the user's savings account after PIN verification.

        Args:
            pin: The user's PIN used to authorize the funding request.
            amount: The amount to add to the savings account.
            user: The user whose savings account will be funded.

        Returns:
            A ``QuickFundResponse`` describing the result of the funding
            request.

        Raises:
            NotImplementedError: If savings account funding has not yet been
                implemented.
        """
        raise NotImplementedError("Savings account funding is not implemented yet.")

