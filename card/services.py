from __future__ import annotations

import logging

from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from bank.models import BankAccount
from .models import BankCard
from utils.custom_errors import BankAccountTypeError
from utils.security.generator import generate_secure_code


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


