from __future__ import annotations
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from bank.models import (SortCodeRangePool,
                         SortCodeAllocationStateLog,
                         Bank, 
                         BankAccount,
                          SortCodeAllocationState, 
                          SortCodeAllocatorLastRecordLookup,
                          SortCode)
from user_profile.models import UserProfile
from utils.security.generator import generate_secure_code



class BankProvisioningService:
    """
    Creates and fully provisions a new Bank instance.

    This method performs the complete bank onboarding workflow within
    a single database transaction to ensure atomicity. If any step fails,
    the transaction is rolled back and no partial provisioning is persisted.

    Expected bank_data fields:
        {
            "name": str,
            "country": str,
            "description": str,
            "logo": InMemoryUploadedFile | File,
            "branch_name": str,
            "address_line_1": str,
            "address_line_2": str,
            "post_code": str,
            "interest_period": str,
            "phone_number": str,
            "minimum_opening_deposit": Decimal,
            "offer_overdraft": str,
            "offer_saving_account": str,
            "monthly_deposit": Decimal,
        }

    Workflow:
        1. Creates the Bank entity.
        2. Generates and assigns a unique bank code.
        3. Attempts to claim an available sort code range block.
        4. Allocates a new sort code block if none are available.
        5. Creates the bank sort code range record.
        6. Logs the allocation event for auditing purposes.

    Args:
        bank_data (dict):
            Validated bank data used to create the Bank instance.
            Typically sourced from a Django ModelForm's cleaned_data.

    Returns:
        Bank:
            The fully provisioned Bank instance ready for use.

    Raises:
        ValueError:
            - If bank_data is not a dictionary.
            - If a sort code range cannot be allocated.

    Important:
        This service MUST be used to create banks in production.

        Direct creation via `Bank.objects.create()` is not safe because it bypasses:
        - sort code range allocation
        - pool reuse logic
        - allocation state tracking
        - audit logging of provisioning decisions

        All Bank instances must be provisioned through this service to ensure
        consistency and integrity of the banking system.
    """
    @classmethod
    def _create_bank_instance(cls, bank_data: dict) -> Bank:
        name = bank_data.get("name")
        bank = Bank(
                **bank_data,
                 bank_code = name[0:2] + generate_secure_code(),
            )
        bank.save()
        return bank
    
    @staticmethod
    def create_bank(bank_data:dict) -> Bank:
        """
        Creates and fully provisions a new Bank instance.

        This method performs the complete bank onboarding workflow:

        1. Creates the Bank entity

        And allocations a bunch of sort codes it can use
       
        The entire operation is executed within a database transaction to ensure
        atomicity. If any step fails, no partial bank provisioning is persisted.

        Returns:
            Bank: The fully provisioned bank instance ready for use.

        Raises:
            ValueError: If input validation fails or no sort code range can be allocated.
        """
        if not isinstance(bank_data, dict):
            raise ValueError(_(f"The bank data must be a dictionary. Expected a dict got type {type(bank_data).__name__}"))
        
      
        reassigned = False
        msg        = None

        with transaction.atomic():

            SortCodeAllocatorLastRecordLookup.objects.get_or_create(
                    pk=1,
                    defaults={"block_size": settings.SORT_CODE_ALLOCATION_BLOCK},
            )

            bank = BankProvisioningService._create_bank_instance(bank_data)

            sortcode_block = SortCodeRangePool.get_available()

            if sortcode_block:
                reassigned  = True
                msg         = "Reassigned a sortcode block"

                sortcode_block.is_claimed = True
                sortcode_block.claimed_by = bank
                sortcode_block.save()
            else:
                sortcode_block = SortCodeAllocationState.create_allocate_sortcode_range(bank=bank)
              
            if not (sortcode_block):
                raise ValueError(_("Expected a sortcode range but got nothing"))
        
            SortCode.objects.create(bank=bank)
            
            if not reassigned:
                msg = "Assigned a new sortcode block"
            
            SortCodeAllocationStateLog.objects.create(
                assigned_to=bank,
                description=msg,
                start_range=sortcode_block.start_range,
                end_range=sortcode_block.end_range,

            )
      
        return bank




class AccountService:
    """
    Handles the creation and lifecycle of BankAccount entities within the system.

    This service is responsible for safely opening new bank accounts under a
    specific Bank, ensuring that all required domain rules are enforced during
    account creation.

    Responsibilities:
        - Validates input parameters (bank, user profile, account type)
        - Retrieves the correct SortCode allocation for the bank
        - Generates a sequential account number within the allocated range
        - Creates and persists the BankAccount entity
        - Optionally associates the account with a UserProfile, userProfile can
          be deffered to later

    Important:
        BankAccount instances MUST NOT be created directly via
        `BankAccount.objects.create()`.

        Direct creation bypasses:
        - sort code validation
        - sequential account number generation
        - concurrency safety locks
        - allocation integrity rules

        All account creation MUST be performed through this service to ensure
        consistency, correctness, and safe concurrency handling.
    """

    @staticmethod
    def open_bank_account(*, bank: Bank, user_profile: UserProfile = None, account_type: str ="basic") -> BankAccount:
        """
        Creates and provisions a new BankAccount under a specific Bank.

        This method is responsible for the full lifecycle of opening a bank account,
        including validation, sort code assignment, and account number generation.

        Workflow:
           
            1. Generates the next sequential sort code  and account number within the bank's allocated range.
            2. Creates and persists a new BankAccount instance.
            3. Optionally associates the account with a UserProfile.

        This entire operation is executed inside a database transaction to guarantee
        atomicity and prevent race conditions during sort code generation and account
        creation.

        Important:
            All BankAccount instances MUST be created through this service.

            Direct creation via `BankAccount.objects.create()` is not safe because it
            bypasses:
                - sort code locking and sequential generation
                - Does not create an account number
                - allocation range constraints
                - concurrency safety guarantees
                - domain validation rules

        Args:
            bank (Bank): The bank under which the account is being created.
            user_profile (UserProfile, optional): Optional user associated with the account.
            account_type (str): Type of account to create. Must be one of:
                "basic", "premium", or "savings".

        Returns:
            BankAccount: A fully initialised and persisted bank account.

        Raises:
            TypeError: If `bank` or `user_profile` are not valid domain instances.
            ValueError: If the account type is invalid or no sort code exists for the bank.
        """

        if user_profile is not None and not isinstance(user_profile, UserProfile):
            raise TypeError(_(f"Expected the user_profile instance to be type UserProfile. Got profile with type {type(UserProfile.__name__)}"))
        
        if not isinstance(bank, Bank):
            raise TypeError(_(f"Expected the bank instance to be type Bank. Got bank with type {type(Bank.__name__)}"))
        
        EXPECTED_CHOICES = [BankAccount.AccountType.BASIC.value, 
                                 BankAccount.AccountType.PREMIUM.value, 
                                 BankAccount.AccountType.SAVINGS.value]
        
        if not (account_type in EXPECTED_CHOICES):
            raise ValueError(_(f"The account_type must be one of the following options {EXPECTED_CHOICES}. Got {account_type}"))
    
        
        with transaction.atomic():
            try:
                sort_code_obj = (
                    SortCodeAllocationState.objects
                    .select_for_update()
                    .get(bank=bank)
                )
            except SortCodeAllocationState.DoesNotExist:
                raise ValueError(_("No sort code found for this bank"))

            allocation_sort_code_block = sort_code_obj.generate_sort_code()

            sort_code = SortCode.objects.create(
                bank=bank,
                external_sort_code=allocation_sort_code_block.external_sortcode,
            )

            bank_account = BankAccount(
                sort_code=sort_code,
                account_number=allocation_sort_code_block.account_number,
                account_type=account_type,
            )
           
            if user_profile:
                bank_account.user_profile = user_profile
            
            bank_account.save()
            return bank_account   