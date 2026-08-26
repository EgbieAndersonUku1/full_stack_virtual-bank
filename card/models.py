from __future__ import annotations

from django.db.models.query import QuerySet
from django.db.models import Prefetch
from django.db import models
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from typing import Iterable, Type, Any, Literal


from bank.models import BankAccount
from utils.custom_errors import BankAccountTypeError, IncorrectAmountError, IncorrectAmountTypeError
from utils.security.generator import generate_secure_code
from utils.validators.validators import validate_amount

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

    card_id           = models.CharField(max_length=32, unique=True, blank=True, null=True)
    full_name         = models.CharField(max_length=32)
    bank_account      = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="cards")
    card_number       = models.CharField(max_length=32, unique=True)
    expiry_date       = models.DateTimeField(blank=True, null=True, editable=False)
    card_brand        = models.CharField(max_length=20, choices=CardBrand.choices, default=CardBrand.VISA)
    card_type         = models.CharField(max_length=20, choices=CardType.choices, default=CardType.VIRTUAL)
    card_category     = models.CharField(max_length=20, choices=CardCategory.choices, default=CardCategory.DEBIT)
    is_active         = models.BooleanField(default=True)
    created_on        = models.DateTimeField(auto_now_add=True)
    last_modified_on  = models.DateTimeField(auto_now=True)
    show_in_dashboard = models.BooleanField(default=False)
    default_card      = models.BooleanField(default=False)

    @property
    def bank_name(self):
        return self.bank_account.bank_name

    @property
    def bank_balance(self):
        return self.bank_account.balance

    @property
    def mask_card_number(self):
        return f"**** **** **** {self.card_number[-4:]}"

    @property
    def user(self):
        return self.bank_account.user_profile.user

    @classmethod
    def _base_queryset(cls) -> QuerySet["BankCard"]:
        """Return the base BankCard queryset with related objects preloaded."""

        return cls.objects.select_related(
            "bank_account",
            "bank_account__sort_code__bank",
            "bank_account__user_profile__user"
        )

    @classmethod
    def get_default_card(cls, bank_account: BankAccount) -> BankCard:
        """
        Return the default card associated with the bank account.

        Args:
            bank_account: The bank account associated with the default card

        Returns:
            The bank card instance associated with bank account.
        """
        cls._validate_type(parameter_name="bank account",
                            parameter_value=bank_account,
                            expected_type=BankAccount
                            )

        return cls._base_queryset().filter(
                                        bank_account=bank_account,
                                        is_active=True
                                         ).first()

    @classmethod
    def get_by_card_type(cls, bank_account: BankAccount, card_type: card_type) -> BankCard:
        cls._validate_type(parameter_name="bank account",
                            parameter_value=bank_account,
                            expected_type=BankAccount
                            )

        if not isinstance(card_type, str):
            error_msg = "Expected a string, got type {}".format(type(card_type).__name__)
            raise TypeError(_(error_msg))

        return cls._base_queryset().filter(
            bank_account=bank_account,
            is_active=True,
            card_type=card_type
        ).order_by("created_on", "id").first()




    @classmethod
    def get_num_of_cards_in_dashboard(cls, bank_account: BankAccount) -> int:
        """Displays the number of cards that bank account has on display in the dashboard"""
        return cls.get_dashboard_cards(bank_account).count()

    @classmethod
    def get_dashboard_cards(cls, bank_account: BankAccount) -> QuerySet["BankCard"]:
        """
        Return cards for the bank account configured to be displayed on the dashboard.
        Only returns cards that are active.
        """

        cls._validate_type(parameter_name="bank account",
                           parameter_value=bank_account,
                           expected_type=BankAccount
                           )

        return cls._base_queryset().filter(
            bank_account=bank_account,
            show_in_dashboard=True,
            is_active=True,
        )

    @classmethod
    def get_by_bank_account(cls, bank_account: BankAccount) -> QuerySet["BankCard"]:
        """Return all bank cards associated with the given bank account."""

        cls._validate_type(
            parameter_name="Bank account",
            parameter_value=bank_account,
            expected_type=BankAccount,
        )

        return cls._base_queryset().filter(bank_account=bank_account)

    @classmethod
    def get_by_bank_account_and_card_number(cls, card_number: str, bank_account: BankAccount) -> BankCard | None:
        """Return the bank card with the given card number, or None if not found."""

        cls._validate_type(
            parameter_name="Card number",
            parameter_value=card_number,
            expected_type=str,
        )

        return cls._base_queryset().filter(
            bank_account=bank_account,
            card_number=card_number,
        ).first()

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

    def save(self, *args, **kwargs) -> None:
        if not self.card_id:
            self.card_id = generate_secure_code(code_length=24)
        super().save(*args, **kwargs)



class CardDashboard(models.Model):
    bank_account      = models.OneToOneField(BankAccount, on_delete=models.CASCADE, related_name="dashboard_cards")
    max_cards_to_show = models.PositiveSmallIntegerField(default=3)
    created_on         = models.DateTimeField(auto_now_add=True)
    last_modified_on   = models.DateTimeField(auto_now=True)

    @property
    def displayed_card_count(self) -> int:
        return len(self.bank_account.dashboard_cards)

    @property
    def can_add_card_to_dashboard(self):
        return self.displayed_card_count >= self.max_cards_to_show

    @classmethod
    def get_by_bank_account(cls, bank_account: BankAccount) -> CardDashboard | None:

        if not isinstance(bank_account, BankAccount):
            error_msg = _("Expected a bank account object. Got type {}".format(type(bank_account).__name__))
            raise BankAccountTypeError(error_msg)

        try:
            return (
                cls.objects
                .select_related("bank_account")
                .prefetch_related(
                    Prefetch(
                        "bank_account__cards",
                        queryset=BankCard.objects.filter(show_in_dashboard=True),
                        to_attr="dashboard_cards",
                    )
                )
                .get(bank_account=bank_account)
            )
        except cls.DoesNotExist:
            return None

    def __str__(self) -> str:
        return self.bank_account.full_name



card_type = Literal[BankCard.CardBrand.DISCOVER,
                    BankCard.CardBrand.VISA,
                    BankCard.CardBrand.MASTERCARD
                    ]
