from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from bank.models import LedgerEntry
from utils.safe_cache import get_cache_or_set, set_cache_with_retry

User = get_user_model()



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

        key = cls._construct_cache_key(user, page)

        return get_cache_or_set(
            key,
            lambda: cls._fetch(
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
            key = cls._construct_cache_key(user, page)
            data_dict_list = cls._fetch(
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

        key = cls._construct_cache_key(user, page)

        set_cache_with_retry(
            key,
            value=cls._fetch(
                user,
                limit=cls.PAGE_SIZE,
                offset=(page - 1) * cls.PAGE_SIZE,
            ),
            ttl=cls.CACHE_TTL,
        )

    @classmethod
    def _fetch(cls, user: User, limit: int, offset: int) -> list[dict]:
        """
        Fetch a page of ledger transactions directly from the database.
        """
        return list(

            LedgerEntry.get_user_ledger(
                user,
                limit=limit,
                offset=offset,
            ).values(
                "id",
                "transaction_type",
                "movement",
                "amount",
                "opening_balance",
                "closing_balance",
                "created_on",
                "status",
            )
        )

    @classmethod
    def _construct_cache_key(cls, user: User, page: int) -> str:
        """
        Construct the cache key for a user's transaction page.
        """
        return (
            f"ledger_entries__{user.id}"
            f"__recent_transactions__page_{page}"
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

