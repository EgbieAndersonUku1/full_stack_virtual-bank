from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from bank.models import BankAccount, LedgerEntry
from bank.services.services import BankAccountCacheService
from utils.custom_errors import MissingCurrentAccountError

from utils.security.generator import generate_secure_code as generate_reference

User = get_user_model()


class FundingService:
    RISK_THRESHOLD = Decimal("10000.00")

    @classmethod
    def _validate_user(cls, user: User) -> None:
        if not isinstance(user, User):
            error_msg = _("Expected a user instance. Got user with type {}".format(type(user).__name__))
            raise TypeError(error_msg)

    @classmethod
    def _get_current_account_or_raise(cls, user: User) -> BankAccount | None:
        current_account =  BankAccountCacheService.get_current_account(user)

        if not current_account:
            error_msg = _("The current account for user with id {} is missing".format(user.id))
            raise MissingCurrentAccountError(error_msg)

        return current_account


    @classmethod
    def add_funds_to_current_account(cls, amount: Decimal,  user: User) -> BankAccount:
        """
        Add funds to the user's current bank account.

        The supplied amount is credited to the user's current account and a
        corresponding ledger entry is created. If the amount being funded meets or
        exceeds the configured risk threshold, the transaction is flagged for
        review and the account balance is not immediately increased.

        Args:
            amount (Decimal): The positive amount to add to the user's current
                account.
            user (User): The user whose current account will be funded.

        Returns:
            BankAccount: The user's current bank account.

        Raises:
            MissingCurrentAccountError: If the user does not have a current account.
            IncorrectAmountTypeError: If ``amount`` is not a ``Decimal``.
            IncorrectAmountError: If ``amount`` is less than or equal to zero.

        Note:
            ``amount`` should be converted to ``Decimal`` before calling this
            method. In particular, avoid converting through a float when
            constructing a ``Decimal``. For example:

                >>> from decimal import Decimal
                >>> amount = Decimal("200.00")
                >>> FundingService.add_funds_to_current_account(amount, user)
                <BankAccount: ...>
        """

        cls._validate_user(user)
        current_account = cls._get_current_account_or_raise(user)



        with transaction.atomic():

            opening_balance = current_account.balance

            ledger_entry = LedgerEntry(
                reference=f"TX_{generate_reference(code_length=35)}",
                transaction_type=LedgerEntry.TransactionType.ADD_FUNDS,
                source=LedgerEntry.Source.EXTERNAL,
                opening_balance=opening_balance,
                amount=amount,
                currency="GBP", # for now use GBP, later the currency will come from the account when implemented
                description=f"The user {user} funded their account with the amount {amount}",
                movement=LedgerEntry.Movement.CREDIT,
                user=user,
                account=current_account,


            )

            if amount >= cls.RISK_THRESHOLD:
                ledger_entry.risk_flag        = True
                ledger_entry.risk_reason      = f"User {user} funded the account with an amount that exceeded the risk threshold."

                ledger_entry.status           = LedgerEntry.Status.PENDING
                ledger_entry.review_required  = True
            else:

                # Only credit the amount if it hasn't been flagged
                current_account.credit(amount)

                # user's bank account is pending until a successful first time credit is made
                if current_account.status == BankAccount.Status.PENDING:
                    current_account.status = BankAccount.Status.ACTIVE

                current_account.save()
                ledger_entry.status        = LedgerEntry.Status.COMPLETED
                ledger_entry.completed_on  = timezone.now()

            ledger_entry.closing_balance = current_account.balance
            ledger_entry.save()

            return current_account



