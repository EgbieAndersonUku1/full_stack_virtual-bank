from __future__ import annotations

import logging

from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from bank.models import BankAccount
from .models import BankCard, CardDashboard
from utils.custom_errors import BankAccountTypeError
from utils.security.generator import generate_secure_code
from utils.safe_cache import set_cache_with_retry, get_cache_with_retry


logger = logging.getLogger(__name__)


class CardNumberService:

    @staticmethod
    def generate(card_number_length: int = 19) -> str:
        """
        Generates a secure card number.

        Args:
            card_number_length: The number of digits to generate.
                Defaults to 19.

        Returns:
            A securely generated card number as a string.
        """
        return generate_secure_code(code_length=card_number_length)



class BankCardService:

    @staticmethod
    def create_default_bank_card(bank_account: BankAccount) -> BankCard:
        """
        Creates the default bank card for a bank account.

        The default card is a virtual Visa debit card.

        Args:
            bank_account: The bank account the card belongs to.

        Raises:
            BankAccountTypeError: If bank_account is not a BankAccount instance.

        Returns:
            The newly created BankCard instance.
        """
        if not isinstance(bank_account, BankAccount):
            error_msg = _("Expected a bank account instance. Got type {}".format(type(bank_account).__name__))
            raise BankAccountTypeError(error_msg)

        expiry_date              = timezone.now() + timedelta(days=365 * 5) # expires in five years
        DEBIT_CARD_NUMBER_LENGTH = 16

        logger.warning("CREATING DEFAULT CARD | bank_account_id=%s", bank_account.pk)

        return BankCard.objects.create(
            full_name=bank_account.full_name,
            bank_account=bank_account,
            card_number=CardNumberService.generate(DEBIT_CARD_NUMBER_LENGTH),
            expiry_date=expiry_date,
            card_brand=BankCard.CardBrand.VISA,
            card_type=BankCard.CardType.VIRTUAL,
        )





class CardDashboardServiceCache:

    @classmethod
    def construct_session_key(cls, unique_id: str | int) -> str:

        if not (isinstance(unique_id, str) or isinstance(unique_id, int)):
            error_msg = "Expected a string. Got type {}".format(type(unique_id).__name__)
            raise TypeError(_(error_msg))
        return "cards_in_dashboard-{user_id}".format(user_id=unique_id)

    @classmethod
    def get_user_cards(cls, bank_account: BankAccount, session_key_id: int | str) -> list[BankCard]:

        session_key  = cls.construct_session_key(session_key_id)
        cards        = get_cache_with_retry(session_key)

        if not cards:
            dashboard_cards = BankCard.get_dashboard_cards(bank_account)

            if dashboard_cards is not None:
                cards = list(dashboard_cards)
                set_cache_with_retry(session_key, cards)

        return cards
