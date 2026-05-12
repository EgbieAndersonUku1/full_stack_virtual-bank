from django.db import models
from django.db.models import Count
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from django.conf import settings

from user_profile.models import UserProfile
from bank.errors import SortCodeRangeExhaustedError



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

    name                     = models.CharField(max_length=50, unique=True, verbose_name="Bank name*")
    description              = models.TextField(max_length=600, verbose_name="Bank description*") 
    branch_name              = models.CharField(max_length=50, verbose_name="Bank Branch name*")
    address_line_1           = models.CharField(max_length=255, verbose_name="Address line 1*")
    address_line_2           = models.CharField(max_length=255, blank=True, verbose_name="Address line 2")
    phone_number             = PhoneNumberField(verbose_name="Customer support phone number", unique=True)
    post_code                = models.CharField(max_length=11, verbose_name="Bank postcode*")
    country                  = CountryField(blank_label="(select country)", null=True, verbose_name="Bank Country*")
    bank_code                = models.CharField(max_length=20, unique=True, blank=True)
    interest_period          = models.CharField(max_length=20, choices=InterestPeriod.choices,  default=InterestPeriod.MONTHLY, verbose_name="Interest Period*")
    minimum_opening_deposit  = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Minimum opening deposit*")
    monthly_deposit          = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Monthly deposit*")
    last_activity_at         = models.DateTimeField(auto_now=True)
    created_on               = models.DateTimeField(auto_now_add=True)
    last_updated             = models.DateTimeField(auto_now=True)
    offer_overdraft          = models.CharField(max_length=3, choices=OverDraftOptions.choices,
                                                default=OverDraftOptions.NO, 
                                                verbose_name="Offer overdraft*")
    
    offer_saving_account     = models.CharField(max_length=3, choices=OfferSavingAccountOptions.choices, 
                                                default=OfferSavingAccountOptions.NO, 
                                                verbose_name="Offer saving accounts*")
    
    logo = models.FileField(upload_to="bank/logo/", null=True, verbose_name="Bank logo",
                            validators=[FileExtensionValidator(["png", "jpg", "jpeg", "svg"])]
                           )

    # stored in basis points (bank standard for storing)
    interest_rate  = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                        MaxValueValidator(100)],
                                                                        default=0,
                                                                        verbose_name="Interest rate (%)*",
                                                                        )  # 100%
    
    interest_rate_bps        = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                        MaxValueValidator(10000)],
                                                                        default=0,
                                                                      
                                                                        )  # 100%

    def validate_logo_size(file):
        max_size = 2 * 1024 * 1024  # 2MB

        if file.size > max_size:
            raise ValidationError("Logo must be under 2MB.")

    @property
    def interest_rate_percent(self):
        return self.interest_rate_bps / 100
 
    @property
    def bank_accounts_count(self):
        """
        Returns the total number of BankAccount records linked to this Bank
        through its associated SortCode objects.

        Uses an annotated value (`total_bank_accounts`) when available for performance,
        otherwise falls back to a database COUNT query across SortCodes → BankAccounts.
        """
        return getattr(self, "total_bank_accounts", None) \
            or self.sort_codes.aggregate(
                total=Count("bank_accounts")
            )["total"]
        

    @classmethod
    def get_by_bank_name(cls, bank_name: str):
        
        try:
            return cls.objects.get(name=bank_name.title())
        except cls.DoesNotExist:
            return None
        
    def save(self, *args, **kwargs):

        if self.name:
            self.name = self.name.title()

        if self.branch_name:
            self.branch_name = self.branch_name.title()

        return super().save(*args, **kwargs)
    
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
    
    assigned_to = models.ForeignKey(Bank, on_delete=models.DO_NOTHING, related_name="sortcode_allocation_logs")
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
    claimed_by    = models.ForeignKey(Bank, null=True, blank=True, on_delete=models.SET_NULL, related_name="range_pools")
    
    class Meta:
        verbose_name_plural = "Sortcode range pool"
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



class SortCodeAllocatorLastRecordLookup(models.Model):
    """
    A singleton global registry tracking the last allocated sort code block.

    This model stores the most recently issued sort code range (block size,
    start range, and end range) across all banks. It does not belong to any
    specific bank.

    It exists to support sequential, non-overlapping sort code allocation
    across the entire system.

    Difference from SortCodeAllocationState:
    - SortCodeAllocationState is per-bank (OneToOne) and tracks allocations
      for a specific bank.
    - This model is global and ensures new banks do not reuse previously
      allocated sort code ranges.

    When a new bank is created, SortCodeAllocationState uses this model to:
    - Retrieve the last allocated range
    - Generate the next sequential block
    - Persist the updated global allocation state

    This prevents duplicate sort code and account number collisions across banks.
    """
    singleton_key  = models.BooleanField(default=True, unique=True, editable=False)
    block_size     = models.PositiveBigIntegerField()
    start_range    = models.PositiveBigIntegerField(default=0)
    end_range      = models.PositiveBigIntegerField(default=0)
    created_on     = models.DateTimeField(auto_now_add=True)
    last_updated   = models.DateTimeField(auto_now=True)

    @classmethod
    def get_instance(cls):
        """A singleton that returns the instance of records"""

        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(
            singleton_key=True,
            defaults={
                "block_size": settings.SORT_CODE_ALLOCATION_BLOCK,
                "start_range": 0,
                "end_range": 0,
            }
        )

        return obj
           

    


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
    bank                        = models.OneToOneField(Bank, on_delete=models.CASCADE, 
                                                       related_name="sortcode_allocator",
                                                       blank=True, null=True)
    block_size                  = models.PositiveBigIntegerField(blank=True, null=True)
    start_range                 = models.PositiveBigIntegerField(default=0)
    end_range                   = models.PositiveBigIntegerField(blank=True, null=True)
    last_issued_sortcode_number = models.PositiveBigIntegerField(default=0)
    last_issued_account_number  = models.PositiveBigIntegerField(default=0)
    created_on                  = models.DateTimeField(auto_now_add=True)
    last_updated                = models.DateTimeField(auto_now=True)

    @classmethod
    def _calculate_next_range_from_last_record(cls, last_block_record: SortCodeAllocatorLastRecordLookup):
        block_size =  last_block_record.block_size
        start_range = last_block_record.start_range
        end_range   = start_range + block_size
        return start_range, end_range
    
    @classmethod
    def _update_global_range_records(cls, sortcode_record, end_range):
        sortcode_record.start_range = end_range
        sortcode_record.end_range   = end_range + sortcode_record.block_size
        sortcode_record.save()

    @classmethod
    def create_allocate_sortcode_range(cls, bank: Bank):
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

        with transaction.atomic():

            try:
                sortcode_allocator  = cls.objects.select_for_update().get(bank=bank)
            except cls.DoesNotExist:
                sortcode_allocator = None

            if sortcode_allocator:

                block_size   = settings.SORT_CODE_ALLOCATION_BLOCK
                start_range  = sortcode_allocator.end_range + block_size
                end_range    = start_range + block_size

                sortcode_allocator.start_range = start_range
                sortcode_allocator.end_range   = end_range
                sortcode_allocator.save()
            else:

                sortcode_record = SortCodeAllocatorLastRecordLookup.get_instance()
               
                # create new block size from the the record
                start_range, end_range = cls._calculate_next_range_from_last_record(sortcode_record)
             
                sortcode_allocator = cls( 
                    block_size=sortcode_record.block_size,
                    start_range=start_range,
                    end_range=end_range,
                    bank=bank,
                )
                
                # update the last block size with the new a block size 
                cls._update_global_range_records(sortcode_record, end_range)
             
            
                # Initialise allocation counters to the beginning of the assigned
                # block range so all issued sort codes are
                # generated within the bank's allocated identifier namespace.
                sortcode_allocator.last_issued_sortcode_number = start_range
            
                sortcode_allocator.save()

        return sortcode_allocator
    
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

            if self._has_exhausted_block():

                error_msg = "No additional sort codes are available for this allocation block."
                raise SortCodeRangeExhaustedError(_(f"{error_msg}"))
            
            self.last_issued_sortcode_number += 1
            self._issue_next_account_number()
   
            if commit:
                self.save()
                return self
    
    def _has_exhausted_block(self) -> bool:
        """
        Returns True if issuing another sort code would exceed
        the allocated block range.
        """
        return (
            self.last_issued_sortcode_number
            and self.last_issued_sortcode_number + 1 > self.end_range
        )
    
    def _issue_next_account_number(self):
        self.last_issued_account_number += 1
    
    def _total_capacity(self):
        return self.end_range - self.start_range
 
    @property
    def account_number(self):
        """Returns an eight dight in the form of an account number"""
        return str(self.last_issued_account_number).zfill(8)
    
    @property
    def external_sortcode(self):
        """Returns an eight dight in the form of an account number"""
        return str(self.last_issued_sortcode_number).zfill(6)

    @property
    def total_sortcode_capacity(self):
        """The total number of sortcode block allocated to the bank"""
        return f"{self._total_capacity():,}"

    @property
    def remaining_sortcodes(self):
        """The remaining sortcodes remaining"""
        issued = int(self.last_issued_sortcode_number - self.block_size)
        return  f"{self._total_capacity() - issued:,}"

    @property
    def issued_sortcodes_count(self):
        """The number of sortcodes used so far"""
        return f"{self.last_issued_sortcode_number: ,}"

    @property
    def allocation_utilisation_percent(self):
        """The number of sortcodes used as a percentage. Returns the 
           percentage to three decimal places
        """
        issued = self.last_issued_sortcode_number
        total  = self._total_capacity()

        if total == 0:
            return "0.00"
        
        issued = Decimal(self.last_issued_sortcode_number or 0)
        percentage = (issued / Decimal(total)) * Decimal("100")

        return f"{percentage.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP):,}%"

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
    bank                 = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="sort_codes", blank=True, null=True)
    external_sort_code   = models.CharField(max_length=20, unique=True, blank=True, null=True)
    created_on           = models.DateTimeField(auto_now_add=True)
    last_updated         = models.DateTimeField(auto_now=True)

    @property
    def formatted(self):
        if not self.external_sort_code:
            return None
        return f"{self.external_sort_code[:2]}-{self.external_sort_code[2:4]}-{self.external_sort_code[4:]}"
  
    def __str__(self):
        return f"{self.external_sort_code}"
   


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

    sort_code         = models.ForeignKey(SortCode, on_delete=models.PROTECT, related_name="bank_accounts", blank=True, null=True)
    account_number    = models.CharField(max_length=8, editable=False)
    user_profile      = models.ForeignKey(UserProfile, on_delete=models.PROTECT, blank=True, null=True, related_name="bank_accounts")
    balance           = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    last_interest_run = models.DateTimeField(null=True, blank=True)
    account_type      = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.BASIC)
    status            = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    interest_enabled  = models.BooleanField(default=False)
    created_on        = models.DateTimeField(auto_now_add=True)
    last_updated      = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
               fields=["sort_code", "account_number"],
                name="unique_account_per_sortcode"
            )
        ]
    
   
    def __str__(self):
        return str(self.account_number)
    
    @property
    def bank_name(self):
        return self.sort_code.bank.name

    def clean(self):
        if self.pk is None and not self.sort_code:
            raise ValidationError({
                "sort_code": "BankAccount must be created via AccountService"
            })
        
    def save(self, *args, **kwargs):
        self.full_clean()

        super().save(*args, **kwargs)
