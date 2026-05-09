from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_countries.fields import CountryField
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from typing import Optional
from django.conf import settings

from user_profile.models import UserProfile


# Create your models here.

class Bank(models.Model):
    """
    Represents a financial institution within the banking platform.

    Banks are expected to be created through the BankProvisioningService class, 
    this ensures that the required operational resources such as sort code allocation ranges 
    and initialization state are also created.

    Direct creation of Bank instances bypasses provisioning workflows
    and may result in incomplete system configuration such as bank not having
    a range of sortcodes to use.
    """

    class InterestPeriod(models.TextChoices):
        DAILY = "DAILY", _("Daily")
        WEEKLY = "WEEKLY", _("Weekly")
        BI_WEEKLY = "BI_WEEKLY", _("Bi-Weekly")
        MONTHLY = "MONTHLY", _("Monthly")
        YEARLY = "YEARLY", _("Yearly")
    
    class OverDraftOptions(models.TextChoices):
        YES = "Yes", _("Yes")
        NO  = "No", _("No")

    class OfferSavingAccountOptions(models.TextChoices):
        YES = "Yes", _("Yes")
        NO  = "No", _("No")

    name                     = models.CharField(max_length=50, unique=True, verbose_name="Bank name")
    description              = models.TextField(max_length=600, verbose_name="Bank description") 
    branch_name              = models.CharField(max_length=50)
    address_line_1           = models.CharField(max_length=255, blank=True, verbose_name="Address line 1")
    address_line_2           = models.CharField(max_length=255, blank=True, verbose_name="Address line 2")
    phone_number             = models.CharField(max_length=20, blank=True)
    post_code                = models.CharField(max_length=11, blank=True)
    country                  = CountryField(blank_label="(select country)", null=True, blank=True)
    bank_code                = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    interest_period          = models.CharField(max_length=20, choices=InterestPeriod.choices, default=InterestPeriod.MONTHLY)
    minimum_opening_deposit  = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    monthly_deposit          = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    last_activity_at         = models.DateTimeField(auto_now=True)
    created_on               = models.DateTimeField(auto_now_add=True)
    last_updated             = models.DateTimeField(auto_now=True)
    offer_overdraft          = models.CharField(max_length=3, choices=OverDraftOptions.choices, default=OverDraftOptions.NO)
    offer_saving_account     = models.CharField(max_length=3, choices=OfferSavingAccountOptions.choices, default=OfferSavingAccountOptions.NO)
    logo                     = models.ImageField(upload_to="bank/logo/", blank=True, null=True)

     # stored in basis points (bank standard for storing)
    interest_rate_bps        = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                        MaxValueValidator(10000)],
                                                                        default=0,
                                                                        )  # 100%]

    @property
    def interest_rate_percent(self):
        return self.interest_rate_bps / 100

    def set_interest_rate_percent(self, percent):
        self.interest_rate_bps = int(round(percent * 100))

   
    def __str__(self):
        return self.name
    
  

class SortCodeAllocationStateLog(models.Model):
    """
    Audit log for sort code allocation operations within the banking system.

    Records the allocation of sort code ranges assigned to banks during
    provisioning or allocation workflows. This model exists to provide
    traceability, historical visibility, and operational auditing of
    sort code range distribution across financial institutions.

    Each log entry represents a discrete allocation event, including
    the assigned bank, allocation range boundaries, and descriptive
    context about the operation performed.
    """
    
    assigned_to  = models.ForeignKey(Bank, on_delete=models.DO_NOTHING)
    description  = models.CharField(max_length=255)
    start_range  = models.PositiveBigIntegerField(blank=True, null=True)
    end_range    = models.PositiveBigIntegerField(blank=True, null=True)
    created_on   = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)


class SortCodeRangePool(models.Model):
    """
    Represents a pool of previously allocated sort code ranges that have
    been released and are available for reassignment.

    These ranges typically become available when a bank is deprovisioned
    or when a previously allocated block is returned to the system.

    Before allocating a new sort code block to a bank, the system checks
    this model for any reusable ranges. If available, a range is assigned
    from this pool. If no reusable ranges exist, a new range is generated
    via SortCodeAllocationState.
    """
    start_range   = models.PositiveBigIntegerField()
    end_range     = models.PositiveBigIntegerField()
    created_on    = models.DateTimeField(auto_now_add=True)
    last_updated  = models.DateTimeField(auto_now=True)
    is_claimed    = models.BooleanField(default=False)
    claimed_on    = models.DateTimeField(auto_now=True)
    claimed_by  = models.ForeignKey(Bank, null=True,blank=True, on_delete=models.SET_NULL)
 
    @classmethod
    def get_available(cls):

        with transaction.atomic():

            block = (
                cls.objects
                .select_for_update()
                .filter(is_claimed=False)
                .order_by("created_on")
                .first()
            )

        return block




class SortCodeAllocationState(models.Model):
    """
    Tracks the current allocation state for generating new sort code ranges.

    This model maintains the progression of the system-wide sort code range
    allocator. It records the most recently allocated range boundaries and is
    used as the source of truth when generating new, non-overlapping sort code
    blocks.

    When no reusable ranges are available in the SortCodeRangePool, this state
    is used to calculate and allocate a new sequential block of sort codes, this
    ensures that global uniqueness, sequential accounts and preventing 
    range collisions across banks.

    It effectively acts as the "cursor" for the next available sort code range
    in the system.
    """

    block_size    = models.PositiveBigIntegerField(blank=True, null=True)
    start_range   = models.PositiveBigIntegerField(default=0)
    end_range     = models.PositiveBigIntegerField(blank=True, null=True)
    created_on    = models.DateTimeField(auto_now_add=True)
    last_updated  = models.DateTimeField(auto_now=True)

    @classmethod
    def allocate_next_range(cls):
        """
        Allocates the next sequential sort code range block for bank provisioning.

        The system divides the global sort code space into fixed-size blocks.
        Each call to this method advances the allocation cursor and reserves
        a new, non-overlapping range for a bank.

        If no allocation state exists, the first block is created starting at zero.
        Otherwise, the next block is calculated by incrementing the previous
        allocation range.

        This ensures that each bank receives a unique sort code range and prevents
        collisions across the system.
        """

        block_size = settings.SORT_CODE_ALLOCATION_BLOCK

        with transaction.atomic():

            try:
                sortcode_allocator  = cls.objects.select_for_update().get(pk=1)
            except cls.DoesNotExist:
                sortcode_allocator = None

            if sortcode_allocator:
                start_range  = sortcode_allocator.end_range + block_size
                end_range    = start_range + block_size

                sortcode_allocator.start_range = start_range
                sortcode_allocator.end_range   = end_range
                sortcode_allocator.save()
            else:
                start_range = 0
                end_range   = start_range + block_size
                
                sortcode_allocator = cls.objects.create(end_range=end_range,
                                                        block_size=block_size
                                                        )

        return sortcode_allocator
    
    def save(self, *args, **kwargs):

        if self.pk:
            original = type(self).objects.get(pk=self.pk)

            if original.block_size != self.block_size:
                raise ValidationError(
                    _("Block size cannot be changed after creation.")
                )

        super().save(*args, **kwargs)

            
     
class SortCode(models.Model):
    """
    Represents a bank-specific sort code allocation block and issuance tracker.

    Each SortCode instance defines a reserved numeric range assigned to a single bank.
    This range is used to generate sequential sort code numbers and associated
    account identifiers in a controlled and non-overlapping manner.

    The model tracks:
    - the allocated numeric block (block_start → block_end)
    - the last issued sort code within that block
    - the formatted external sort code representation used for banking operations

    This ensures that each bank operates within its own isolated identifier space,
    prevents collisions across the system and maintains deterministic
    sequential generation of sort codes.

    Note:
        Sort codes are generated sequentially within the assigned block and must
        not exceed the allocated range. Once the block is exhausted, a new block
        must be provisioned via the allocation system.
    """
    bank                       = models.ForeignKey(Bank, on_delete=models.CASCADE)
    sort_code                  = models.CharField(max_length=20, unique=True, blank=True, null=True)
    block_start                = models.PositiveBigIntegerField(default=0)
    block_end                   = models.PositiveBigIntegerField(default=0)
    last_issued_sortcode_number = models.PositiveBigIntegerField()
    created_on                  = models.DateTimeField(auto_now_add=True)
    last_updated                = models.DateTimeField(auto_now=True)

    @property
    def total_sortcodes_available(self):
        return self.block_end - self.block_start
    
    @property
    def formatted(self):
        return f"{self.sort_code[:2]}-{self.sort_code[2:4]}-{self.sort_code[4:]}"

    @classmethod
    def get_by_bank_or_name(cls, bank: Optional[Bank | str]):
        """"""
    
        if isinstance(bank, str):
            return cls.objects.get(name=bank)
        
        if isinstance(bank, Bank):
            try:
                return cls.objects.get(bank=bank)
            except cls.DoesNotExist:
                return None
        
        raise ValueError(_(f"Value must either a string or a bank object. Got type {type(bank).__name__}"))
    
    def generate_sort_code(self, commit: bool = True):
        """
        Generates the next sequential sort code within the allocated range for this bank.

        This method increments the last issued sort code number and assigns a new
        unique sort code within the bank's allocated block range.

        The generation is strictly bounded by `block_start` and `block_end` to ensure
        that no sort code is issued outside the allocated range. If the next value
        would exceed the allowed range, the method raises an error to prevent
        overflow and maintain allocation integrity.

        Args:
            commit (bool): If True, the updated sort code state is persisted to the database.
                If False, the instance is updated in-memory only. This allows the instance
                to be saved later and not immediately.

        Raises:
            ValueError: If the next sort code exceeds the allocated block range.

        Returns:
            SortCode: The updated SortCode instance with the newly generated sort code.
        """
        with transaction.atomic():

            if self.last_issued_sortcode_number and self.last_issued_sortcode_number + 1 > self.block_end:

                # for now use valueError, will create a custom error
                raise ValueError(_(f"You have exceed the range of sort codes available to this bank. Total available: {self.total_sortcodes_available}"))
            
            self.last_issued_sortcode_number += 1
            self.sort_code = str(self.last_issued_sortcode_number).zfill(6)

            if commit:
                self.save()
                return self

    def save(self, *args, **kwargs):
        if self.last_issued_sortcode_number is None:
            self.last_issued_sortcode_number = self.block_start

        if not self.last_issued_sortcode_number:
            self.generate_sort_code(commit=False)
        
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.bank}:{self.formatted}"
   


class BankAccount(models.Model):
    """
    Represents a customer bank account within a specific sort code range for a given bank.

    A BankAccount is a domain-level entity that is always associated with a
    SortCode, which defines the valid numeric space in which its account number
    is generated. Each account number is unique within its sort code context.

    This model holds the financial state of the account, including balance,
    account type, status, and optional linkage to a user profile.

    Important:
        BankAccount instances should NOT be created directly using
        `BankAccount.objects.create()`.

        Direct creation bypasses critical domain rules such as:
        - sort code sequential assignment
        - account number generation
        - account number sequential generations
        - allocation safety constraints
        - account number sequential assignment

        Instead, BankAccount creation must be performed through the
        AccountService, which ensures:

        - a valid SortCode is assigned
        - account numbers are generated safely and sequentially
        - concurrency rules and allocation constraints are respected

        The recommended entry point is:
            AccountService.create_account(bank=..., user_profile=...)

    This ensures the integrity of the banking system and prevents creation of
    incomplete or invalid financial records.
    """

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
    account_number    = models.CharField(max_length=8, editable=False)
    user_profile      = models.ForeignKey(UserProfile, on_delete=models.PROTECT, blank=True, null=True)
    balance           = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    last_interest_run = models.DateTimeField(null=True, blank=True)
    account_type      = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.BASIC)
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
    


