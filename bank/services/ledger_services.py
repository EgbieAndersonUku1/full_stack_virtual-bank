import logging
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from bank.models import LedgerEntry
from utils.safe_cache import set_cache_with_retry, get_cache_with_retry
from utils.validators.validators import validate_user, validate_amount

User = get_user_model()

logger = logging.Logger(__name__)

class LedgerEntryCache:

    @classmethod
    def get_pending_amount_or_refresh(cls, user: User) -> Decimal:
        """
        Return the user's total pending funding amount from the cache.

        If the pending amount is not present in the cache, the value is
        retrieved from the database and the cache is refreshed before the
        amount is returned.

        This method keeps the cache as the primary source for repeated reads
        while allowing callers such as context processors to initialise or
        restore the cached value when it is unavailable.

        Args:
            user (User): The user whose pending funding amount should be
                retrieved.

        Returns:
            Decimal: The user's total pending funding amount. Returns
                ``Decimal("0.00")`` if no pending funding transactions exist.

        Raises:
            TypeError: If ``user`` is not a valid User instance.
        """
        validate_user(user)

        key = cls._construct_session_key(user)

        pending_amount = get_cache_with_retry(key=key)

        if pending_amount is not None:
            return pending_amount

        pending_amount = LedgerEntry.get_pending_funding_amount_for_user(user)

        logging.debug(f"Amount not found get amound from database and then caching for user {user.id}")
        cls.set_pending_amount(pending_amount, user)

        return pending_amount

    @classmethod
    def set_pending_amount(cls, amount: Decimal, user: User) -> None:
        """
        Return the user's pending funding amount from the cache.

        Args:
            user (User): The user whose pending funding amount should be
                retrieved.

        Returns:
            Decimal: The cached pending funding amount.

        Raises:
            TypeError: If ``user`` is not a valid User instance.
        """

        validate_user(user)
        if not isinstance(amount, Decimal):
            error_msg = f"Expected a decimal oject got type {type(amount).__name__}"
            raise TypeError(_(error_msg))

        logging.debug(f"Adding the amount {amount} to the ledger entry cache for user {user.id}")
        set_cache_with_retry(
            key=cls._construct_session_key(user),
            value=amount
        )

    @classmethod
    def _construct_session_key(cls, user) -> str:
        return f"ledger_entry__{user.username}_{user.id}"



