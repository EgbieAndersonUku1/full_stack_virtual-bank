from __future__ import annotations
from typing import Any
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils.timezone import datetime
from typing import TypedDict

from bank.models import LedgerEntry
from utils.safe_cache import get_cache_or_set, set_cache_with_retry
from utils.converter import convert_date_string_to_date_object


User = get_user_model()

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

class TransactionServiceBase:

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
            lambda: TransactionServiceBase.fetch(
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
            data_dict_list = TransactionServiceBase.fetch(
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
            value=TransactionServiceBase.fetch(
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
    ) -> dict:
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
            error = "The from date cannot be after the to date."
            # return api to go here

        filtered_data = []

        for transaction in recent_transactions:
            created_on = transaction["created_on"].date()

            if not (from_date_object <= created_on <= to_date_object):
                print("I am here in dates")
                continue

            if transaction["movement"].lower() != movement.lower():
                print("I am here in movement")
                continue

            if transaction["account_type"].lower() != account_type.lower():
                print("I am here in account type")
                continue

            if transaction["status"].lower() != status.lower():
                print("I am here in status")
                continue


            filtered_data.append(transaction)

        print(filtered_data)


        # raise NotImplementedError("The method hasn't been implemented yet")
