from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_countries.fields import CountryField

from django.utils.translation import gettext_lazy as _

from user_profile.models import UserProfile

# Create your models here.

class Bank(models.Model):

    class InterestPeriod(models.TextChoices):
        DAILY = "DAILY", _("Daily")
        WEEKLY = "WEEKLY", _("Weekly")
        BI_WEEKLY = "BI_WEEKLY", _("Bi-Weekly")
        MONTHLY = "MONTHLY", _("Monthly")
        YEARLY = "YEARLY", _("Yearly")

    name                     = models.CharField(max_length=50, unique=True)
    description              = models.TextField(max_length=600) 
    branch_name              = models.CharField(max_length=50)
    address                  = models.TextField(max_length=255)
    country                  = CountryField(blank_label="(select country)")
    identifier               = models.CharField(max_length=20, unique=True, blank=True)
    interest_period          = models.CharField(max_length=20, choices=InterestPeriod.choices, default=InterestPeriod.MONTHLY)
    minimum_opening_deposit  = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_activity_at         = models.DateTimeField(auto_now=True, blank=True)
    created_on               = models.DateTimeField(auto_now_add=True, blank=True)
    last_updated             = models.DateTimeField(auto_now=True, blank=True)
    offer_overdraft          = models.BooleanField(default=False)
    offer_saving_account     = models.BooleanField(default=False)
    logo                     = models.ImageField(upload_to="bank/logo/")

     # stored in basis points (bank standard for storing)
    interest_rate_bps        = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10000)])  # 100%]

    @property
    def interest_rate_percent(self):
        return self.interest_rate_bps / 100

    def set_interest_rate_percent(self, percent):
        self.interest_rate_bps = int(round(percent * 100))
    
  

class SortCode(models.Model):

    bank                = models.ForeignKey(Bank, on_delete=models.CASCADE)
    code                = models.CharField(max_length=6, unique=True)
    last_account_number = models.PositiveIntegerField(default=0)
    last_index          = models.PositiveIntegerField()
    created_on          = models.DateTimeField(auto_now_add=True)
    last_updated        = models.DateTimeField(auto_now=True)

    @property
    def formatted(self):
        return f"{self.code[:2]}-{self.code[2:4]}-{self.code[4:]}"

    def __str__(self):
        return _(f"{self.bank}:{self.formatted}")



class BankAccount(models.Model):

    class AccountType(models.TextChoices):
        BASIC   = "basic", "Basic"
        PREMIUM = "premium", "Premium"
        SAVINGS = "savings", "Savings"
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        RESTRICTED = "restricted", "Restricted"
        INACTIVE = "inactive", "Inactive"

    sort_code         = models.ForeignKey(SortCode, on_delete=models.CASCADE)
    account_number    = models.CharField(max_length=8)
    user_profile      = models.ForeignKey(UserProfile, on_delete=models.PROTECT)
    balance           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_interest_run = models.DateTimeField(null=True, blank=True)
    account_type      = models.CharField(max_length=20, choices=AccountType.choices)
    status            = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    interest_enabled  = models.BooleanField(default=False)
    created_on        = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
               fields=["sort_code", "account_number"],
                name="unique_account_per_sortcode"
            )
        ]
    