from __future__ import annotations

from django.db.models.query import QuerySet
from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from typing import Type, Any


from bank.models import BankAccount
from utils.custom_errors import BankAccountTypeError

# Create your models here.


class BankCard(models.Model):

    class Meta:
        ordering = ["-created_on"]

    class CardType(models.TextChoices):
        VIRTUAL = "virtual", _("Virtual")
        PHYSICAL = "physical", _("Physical")
        TEMPORARY = "temporary", _("Temporary")

    class CardCategory(models.TextChoices):
        CREDIT = "credit", _("Credit")
        DEBIT = "debit", _("Debit")

    class CardBrand(models.TextChoices):
        VISA = "visa", _("Visa")
        MASTERCARD = "mastercard", _("Mastercard")
        DISCOVER = "discover", _("Discover")

    full_name        = models.CharField(max_length=32)
    bank_account     = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="cards")
    card_number      = models.CharField(max_length=32, unique=True)
    expiry_date      = models.DateTimeField(blank=True, null=True, editable=False)
    balance          = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    card_brand       = models.CharField(max_length=20, choices=CardBrand.choices, default=CardBrand.VISA)
    card_type        = models.CharField(max_length=20, choices=CardType.choices, default=CardType.VIRTUAL)
    card_category    = models.CharField(max_length=20, choices=CardCategory.choices, default=CardCategory.DEBIT)
    created_on       = models.DateTimeField(auto_now_add=True)
    last_modified_on = models.DateTimeField(auto_now=True)

    @property
    def mask_card_number(self):
        return f"**** ****{self.card_number[:-4]}"
    
    @classmethod
    def get_by_bank_account(cls, bank_account: BankAccount) -> QuerySet["BankCard"]:

        cls._validate_type(parameter_name="bank account",
                           parameter_value=bank_account,
                           expected_type=BankAccount
                           )

        return cls.objects.filter(bank_account=bank_account)

    @classmethod
    def get_by_card_number(cls, card_number: str) -> BankCard | None:

        cls._validate_type(parameter_name="Card number",
                           parameter_value=card_number,
                           expected_type=str
                           )

        try:
            return cls.objects.get(card_number=card_number)
        except cls.DoesNotExist:
            return None


    @staticmethod
    def _validate_type(parameter_name: str,
                       parameter_value: Any,
                       expected_type: Type[Any]
                       ) -> None:

         if not isinstance(parameter_value, expected_type):
            message = ("Expected {parameter_name} of type {expected_type}, "
                    "but got {received_type}."
                    ).format(
                        parameter_name=parameter_name,
                        expected_type=expected_type.__name__,
                        received_type=type(parameter_value).__name__,
                    )
            error_msg = _(message)
            raise BankAccountTypeError(error_msg)

    def __str__(self) -> str:
        return self.full_name

