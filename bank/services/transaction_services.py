from __future__ import annotations
from decimal import Decimal
from enum import Enum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils.timezone import datetime
from typing import TypedDict
from django.core.paginator import Paginator
from django.conf import settings
from django.db import transaction
from django.conf import settings


from bank.models import LedgerEntry, BankAccount
from bank.services.bank_services import BankAccountCacheService
from utils.custom_errors import InsufficientFundsError, SameAccountError, BankAccountTypeError, CurrencyMismatchError
from utils.formatter import format_currency
from utils.safe_cache import get_cache_or_set, set_cache_with_retry
from utils.converter import convert_date_string_to_date_object
from utils.utils import remove_under_score
from utils.validators.validators import validate_amount, validate_datetime
from utils.security.generator import generate_secure_code as generate_reference



User = get_user_model()

class DataResponse(TypedDict):
    SUCCESS: bool
    ERROR_MSG: str
    SUCCESS_MSG: str
    TRANSACTIONS: list
    NUMBER_RETURNED: int
    ACTION: str
    TOTAL_BALANCE: str




class Start(Enum):
    IMMEDIATELY = "immediately"
    SCHEDULED = "scheduled"


class Recurrence(Enum):
    NONE = None
    DAILY = "daily"
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"


def _is_valid_date_range(from_date: datetime, to_date: datetime):
    """Return True if the date range is valid."""
    return from_date <= to_date



def _construct_recent_transaction_cache_key(user: User, page: int) -> str:
    """
    Construct the cache key for a user's transaction page.
    """
    return (
            f"ledger_entries__{user.id}"
            f"__recent_transactions__page_{page}"
        )



class _TransactionServiceBase:

    @classmethod
    def fetch(cls, user: User, limit: int, offset: int) -> list[dict]:
        """
        Fetch a page of ledger transactions directly from the database.
        """
        return list(
                LedgerEntry.get_user_ledger(
                    user,
                    limit=limit,
                    offset=offset,
                )
                .annotate(account_type=F("account__account_type"))
                .values(
                    "id",
                    "transaction_type",
                    "movement",
                    "amount",
                    "opening_balance",
                    "closing_balance",
                    "created_on",
                    "status",
                    "account_type"
                )
            )

    @staticmethod
    def format_transaction(transaction: dict) -> dict:
        """Format transaction data for display in the frontend.

        Args:
            transaction: The transaction data to format.

        Returns:
            A copy of the transaction data with display-friendly formatting.
        """
        transaction_copy = transaction.copy()

        transaction_copy["transaction_type"] = remove_under_score(transaction["transaction_type"]).title()
        transaction_copy["opening_balance"] = format_currency(transaction["opening_balance"])
        transaction_copy["closing_balance"] = format_currency(transaction["closing_balance"])
        transaction_copy["amount"] = format_currency(transaction["amount"])
        transaction_copy["movement"] = transaction["movement"].title()
        transaction_copy["status"] = transaction["status"].title()
        transaction_copy["created_on"] = transaction["created_on"].strftime(
            "%d %b %Y, %H:%M"
        )

        if transaction["account_type"] == "basic":
            transaction_copy["account_type"] = "current"

        transaction_copy["account_type"] = transaction_copy["account_type"].title()

        return transaction_copy

    @staticmethod
    def total_balance(user: User):
        return format_currency(BankAccountCacheService.get_total_account_balance(user))

    @staticmethod
    def set(session_key : str,
            user: User,
            limit: int,
            page : int = 1,
            page_size : int = 10,
            ttl: int = 300):

        set_cache_with_retry(
                    session_key,
                    value=_TransactionServiceBase.fetch(
                        user,
                        limit=limit,
                        offset=(page - 1) * page_size,
                    ),
                    ttl=ttl,
                )

class UserRecentTransactionsCacheService:
    """
    Provide cached access to a user's recent ledger transactions.

    The service retrieves ledger entries in pages and caches each page
    independently. This prevents repeated database queries when the same
    transaction page is requested within the cache lifetime.

    Each page contains up to ``PAGE_SIZE`` transactions, and cached values
    expire after ``CACHE_TTL`` seconds.

    The service caches concrete transaction data as a list of dictionaries
    rather than a Django QuerySet. This ensures that the cached value is
    evaluated before being stored and avoids relying on QuerySet laziness
    after retrieval from the cache.

    Attributes:
        PAGE_SIZE (int):
            The maximum number of transactions returned per page.

        CACHE_TTL (int):
            The amount of time, in seconds, that a cached page remains
            valid.

    Example:
        Retrieve the first page of recent transactions::

            transactions = UserRecentTransactionsCacheService.get(user)

        Retrieve the second page::

            transactions = UserRecentTransactionsCacheService.get(
                user,
                page=2,
            )

        Explicitly refresh a cached page::

            UserRecentTransactionsCacheService.set(
                user,
                page=1,
            )
    """

    PAGE_SIZE = 10
    CACHE_TTL = 300

    @classmethod
    def get(cls, user: User, page: int = 1) -> list[dict]:
        """
        Return a cached page of the user's recent transactions.

        If the requested page is already cached, the cached value is
        returned without querying the database. If the page is not cached,
        the transactions are fetched from the database, cached, and returned.

        Args:
            user (User):
                The user whose transactions should be returned.

            page (int):
                The page number to retrieve. Pages are one-indexed and
                default to 1.

        Raises:
            TypeError:
                If ``page`` is not an integer.

            ValueError:
                If ``page`` is less than 1.

        Returns:
            list[dict]:
                A list containing the transactions for the requested page.
                Each transaction is represented as a dictionary containing
                the fields required by the consumer.
        """
        cls._validate_page(page)

        key = _construct_recent_transaction_cache_key(user, page)

        return get_cache_or_set(
            key,
            lambda: _TransactionServiceBase.fetch(
                user,
                limit=cls.PAGE_SIZE,
                offset=(page - 1) * cls.PAGE_SIZE,
            ),
            ttl=cls.CACHE_TTL,
        )

    @classmethod
    def get_or_refresh(cls, user: User, page: int = 1) -> list[dict]:
        """"""
        data_dict_list = cls.get(user=user, page=page)

        if not data_dict_list:
            key = _construct_recent_transaction_cache_key(user, page)
            data_dict_list = _TransactionServiceBase.fetch(
                                        user,
                                        limit=cls.PAGE_SIZE,
                                        offset=(page - 1) * cls.PAGE_SIZE,
                                    ),
            set_cache_with_retry(
                        key,
                        value=data_dict_list,
                        ttl=cls.CACHE_TTL,
                    )
        return data_dict_list


    @classmethod
    def set(cls, user: User, page: int = 1) -> None:
        """
        Fetch and cache a page of the user's recent transactions.

        This method always fetches the requested page from the database
        before storing the result in the cache. It is useful when a cached
        page needs to be explicitly refreshed.

        Args:
            user (User):
                The user whose transactions should be cached.

            page (int):
                The page number to fetch and cache. Pages are one-indexed
                and default to 1.

        Raises:
            TypeError:
                If ``page`` is not an integer.

            ValueError:
                If ``page`` is less than 1.
        """
        cls._validate_page(page)

        key = _construct_recent_transaction_cache_key(user, page)

        set_cache_with_retry(
            key,
            value=_TransactionServiceBase.fetch(
                user,
                limit=cls.PAGE_SIZE,
                offset=(page - 1) * cls.PAGE_SIZE,
            ),
            ttl=cls.CACHE_TTL,
        )

    @classmethod
    def _validate_page(cls, page: int) -> None:
        """
        Validate that the requested page number is a positive integer.

        Args:
            page (int):
                The page number to validate.

        Raises:
            TypeError:
                If ``page`` is not an integer.

            ValueError:
                If ``page`` is less than 1.
        """
        if not isinstance(page, int):
            error_msg = (
                f"Expected an integer but got object with type "
                f"{type(page).__name__}"
            )
            raise TypeError(_(error_msg))

        if page < 1:
            error_msg = (
                f"Expected page to be greater than or equal to 1, "
                f"but got {page}"
            )
            raise ValueError(_(error_msg))



class TransactionSearchService:
    """Service for searching and retrieving transactions for a user."""

    @classmethod
    def recent_transaction_search(
        cls,
        page: int = 1,
        *,
        user: User,
        from_date: datetime,
        to_date: datetime,
        movement: str | None = None,
        account_type: str | None= None,
        status: str | None = None,
    ) -> DataResponse:
        """Search for a user's recent transactions using the provided filters.

        Args:
            page: The page number of results to return. Defaults to 1.
            page_size: The maximum number of transactions to return per page.
                Defaults to 10.
            user: The user whose transactions should be searched.
            from_date: The start of the transaction date range.
            to_date: The end of the transaction date range.
            movement: The movement to filter transactions by e.g credit or debit.
            account_type: The account type to filter transactions by.

        Returns:
            The transactions matching the provided search criteria.

        Raises:
            DateTimeError: If from_date or to_date is not a valid datetime.
            TypeError: If movement or account_type is not a string.
            UserError: If the user is invalid or does not meet the requirements
                enforced by the Ledger model.
        """
        recent_transactions = UserRecentTransactionsCacheService.get(user, page)

        to_date_object   = convert_date_string_to_date_object(to_date)
        from_date_object = convert_date_string_to_date_object(from_date)

        if not _is_valid_date_range(from_date, to_date):
            error_msg  = "The from date cannot be after the to date."
            data: DataResponse =  {
                "SUCCESS": False,
                "ERROR_MSG": error_msg,
                "SUCCESS_MSG": "",
                "TRANSACTIONS": [],
                "NUMBER_RETURNED": 0,
                "ACTION": "Invalid date",
                "TOTAL_BALANCE": _TransactionServiceBase.total_balance(user)
            }
            return data

        filtered_data = []

        for transaction in recent_transactions:
            created_on = transaction["created_on"].date()

            if not (from_date_object <= created_on <= to_date_object):
                continue

            if transaction["movement"].lower() != movement.lower():
                continue

            if transaction["account_type"].lower() != account_type.lower():
                continue

            if transaction["status"].lower() != status.lower():
                continue

            formatted_transaction = _TransactionServiceBase.format_transaction(transaction)
            filtered_data.append(formatted_transaction)

        data: DataResponse =  {
                        "SUCCESS": True,
                        "ERROR_MSG": "",
                        "SUCCESS_MSG": "Successfully, retrieved data",
                        "TRANSACTIONS": filtered_data,
                        "NUMBER_RETURNED": len(filtered_data),
                        "ACTION": "Data retrieval",
                        "TOTAL_BALANCE": _TransactionServiceBase.total_balance(user)
                    }

        return data



class TransactionService:

    @staticmethod
    def get_recent_transactions(user : User, page : int = 1) -> DataResponse:

        recent_transactions = UserRecentTransactionsCacheService.get(user, page)

        cleaned_data = []

        for transaction in recent_transactions:

            formatted_transaction = _TransactionServiceBase.format_transaction(transaction)
            cleaned_data.append(formatted_transaction)

        number_returned    = len(cleaned_data)
        is_populated       =  number_returned > 0
        data: DataResponse =  {

                            "SUCCESS": True if is_populated else False,
                            "ERROR_MSG": "",
                            "SUCCESS_MSG": "Successfully, retrieved transactions data" if is_populated else "No transactions found",
                            "TRANSACTIONS": cleaned_data,
                            "NUMBER_RETURNED": number_returned,
                            "ACTION": "Data retrieval",
                            "TOTAL_BALANCE": _TransactionServiceBase.total_balance(user),

                            }
        return data

    @staticmethod
    def get_user_transactions(user: User, page: int, page_size: int):

        ledger_entry_qs = (LedgerEntry.get_user_ledger(
                            user,
                            ).annotate(account_type=F("account__account_type"))
                            .values(
                                "id",
                                "transaction_type",
                                "movement",
                                "amount",
                                "opening_balance",
                                "closing_balance",
                                "created_on",
                                "status",
                                "account_type"
                            )
                    )

        paginator = Paginator(ledger_entry_qs, page_size)
        return paginator.get_page(page)

    @classmethod
    def transfer(
            cls,
            source_account: BankAccount,
            recipient_account: BankAccount,
            amount: Decimal,
            start: Start = Start.IMMEDIATELY,
            recurrence: Recurrence = Recurrence.NONE,
            schedule_date: datetime = None
        ):

        cls._validate_bank_accounts(source_account, recipient_account)
        validate_amount(amount)

        cls._validate_schedule(start, recurrence, schedule_date)
        cls._validate_transfer_currencies(source_account, recipient_account)

        if not cls._has_sufficient_funds(source_account, amount):
            error_msg = "The source account has insufficient funds"
            raise InsufficientFundsError(_(error_msg))

        if start == Start.IMMEDIATELY and recurrence is None:
            cls._handle_transfer(
                source_account=source_account,
                recipient_account=recipient_account,
                amount=amount,
            )




    @classmethod
    def _validate_bank_accounts(cls, account_1: BankAccount,  account_2: BankAccount) -> None:

        if not isinstance(account_1, BankAccount):
            error_msg="Expected bank instance for account_1, got type {}".format(type(account_1).__name__)
            raise BankAccountTypeError( _(error_msg))

        if not isinstance(account_2, BankAccount):
            error_msg="Expected bank instance for account 2, got type {}".format(type(account_2).__name__)
            raise BankAccountTypeError( _(error_msg))

        if account_1 == account_2:
            raise SameAccountError(_("Source account and recipient account cannot be the same"))

    @classmethod
    def _validate_schedule(cls, start: Start, recurrence: Recurrence, schedule_date: datetime = None) -> None:

        if not isinstance(start, Start):
            error_msg = "Start must be an instance of Start, got type {}".format(
                type(start).__name__
            )
            raise TypeError(_(error_msg))

        if not isinstance(recurrence, Recurrence):
            error_msg = "Recurrence must be an instance of Recurrence, got type {}".format(
                type(recurrence).__name__
            )
            raise TypeError(_(error_msg))

        if start == Start.IMMEDIATELY and schedule_date is not None:
            raise ValueError(
                _("A schedule date must not be provided when the start is immediate.")
            )

        if start == Start.SCHEDULED and schedule_date is None:
            raise ValueError(
                _("A schedule date must be provided when the start is scheduled.")
            )

        if start == Start.SCHEDULED and schedule_date is not None:
            validate_datetime(schedule_date)

    @classmethod
    def _validate_transfer_currencies(
            cls,
            source_account: BankAccount,
            destination_account: BankAccount,
        ):

        """
        Validate that both accounts use the same currency for the transfer.

        Raises:
            CurrencyMismatchError: If the source and destination accounts use different currencies.
        """

        if source_account.currency.lower() != destination_account.currency.lower():
            raise CurrencyMismatchError(
                "Source and destination accounts must use the same currency."
            )

    @classmethod
    def _has_sufficient_funds(cls, account: BankAccount, amount: Decimal):

       has_funds = account.available_balance >= amount

       if has_funds:
           return True

       if not account.supports_overdraft:
           return False

       overdraft_limit = cls._get_overdraft_limit(account)

       if account.available_balance + overdraft_limit >= amount:
            return True

       return False

    @classmethod
    def _get_overdraft_limit(cls, account: BankAccount):
        """
        Return the effective overdraft limit for the account.

        The account's stored overdraft_limit is normally used. However, some
        accounts may have been created before the overdraft_limit field was
        introduced and may therefore have a zero value despite supporting
        overdrafts. For backward compatibility, those accounts fall back to
        the configured DEFAULT_OVERDRAFT_LIMIT.

        This ensures existing overdraft-enabled accounts continue to have a
        valid overdraft limit after the field was introduced.
        """

        if account.supports_overdraft:
            overdraft_limit = account.overdraft_limit

        if account.supports_overdraft and overdraft_limit == Decimal("0.00"):
            overdraft_limit = Decimal(str(settings.DEFAULT_OVERDRAFT_LIMIT))

        return overdraft_limit

    @classmethod
    def _handle_transfer(cls, source_account: BankAccount, recipient_account: BankAccount,  amount: Decimal):

        source_account_user    = source_account.user_profile.user
        recipient_account_user = recipient_account.user_profile.user
        is_risk_triggered      = False

        RISK_THRESHOLD_AMOUNT = settings.RISK_THRESHOLD


        def update_caches():
            BankAccountCacheService.set(source_account_user)
            BankAccountCacheService.set(recipient_account_user)

        def update_recent_transactions():
             UserRecentTransactionsCacheService.set(source_account_user)
             UserRecentTransactionsCacheService.set(recipient_account_user)

        with transaction.atomic():

            transfer_reference = generate_reference(code_length=25)
            source_ledger_entry = LedgerEntry(
                            reference=f"TX_{generate_reference(code_length=35)}",
                            transaction_type=LedgerEntry.TransactionType.TRANSFER_OUT,
                            source=LedgerEntry.Source.BANK_TRANSFER,
                            transfer_reference=transfer_reference,
                            opening_balance=source_account.balance,
                            amount=amount,
                            currency=source_account.currency,
                            description=f"The user {source_account_user} is transfer the amount {amount} to the account {recipient_account_user}",
                            movement=LedgerEntry.Movement.DEBIT,
                            user=source_account_user,
                            account=source_account,
                        )

            recipient_ledger_entry = LedgerEntry(
                                    reference=f"TX_{generate_reference(code_length=35)}",
                                    transaction_type=LedgerEntry.TransactionType.TRANSFER_IN,
                                    source=LedgerEntry.Source.BANK_TRANSFER,
                                    transfer_reference=transfer_reference,
                                    opening_balance=recipient_account.balance,
                                    amount=amount,
                                    currency=recipient_account.recipient,
                                    description=f"The user {recipient_account_user} is being credited with the amount {amount}",
                                    movement=LedgerEntry.Movement.CREDIT,
                                    user=recipient_account_user,
                                    account=recipient_account,
                                )

            transaction.on_commit(update_caches)

            if amount >= RISK_THRESHOLD_AMOUNT:

                risk_reason = f"Transfer amount {amount} meets or exceeds the configured risk threshold {RISK_THRESHOLD_AMOUNT}"

                source_account.update_reserved_amount(amount)
                source_ledger_entry.risk_flag   = True
                source_ledger_entry.risk_reason = risk_reason

                source_ledger_entry.status          = LedgerEntry.Status.PENDING
                source_ledger_entry.review_required = True

                # recipient ledger
                recipient_ledger_entry.risk_flag = True
                recipient_ledger_entry.risk_reason = risk_reason

                recipient_ledger_entry.status          = LedgerEntry.Status.PENDING
                recipient_ledger_entry.review_required = True

                is_risk_triggered = True

                source_account.save()

            else:
                source_account.debit(amount)
                recipient_account.credit(amount)

                source_account.save()
                recipient_account.save()

                completed_time                   = timezone.now()
                source_ledger_entry.status       = LedgerEntry.Status.COMPLETED
                source_ledger_entry.completed_on = completed_time

                recipient_ledger_entry.status       = LedgerEntry.Status.COMPLETED
                recipient_ledger_entry.completed_on = completed_time

            source_ledger_entry.closing_balance    = source_account.balance
            recipient_ledger_entry.closing_balance = recipient_account.balance

            source_ledger_entry.save()
            recipient_ledger_entry.save()

            transaction.on_commit(update_recent_transactions)

        if is_risk_triggered:
            pass
