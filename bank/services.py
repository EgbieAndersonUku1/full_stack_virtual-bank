from __future__ import annotations
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from bank.models import (SortCodeRangePool,
                         SortCodeAllocationStateLog,
                         Bank, 
                         BankAccount,
                          SortCodeAllocationState, 
                          SortCode)
from user_profile.models import UserProfile
from utils.security.generator import generate_secure_code



class BankProvisioningService:
    """
    Handles the creation and provisioning of Bank entities within the system.

    This service is responsible for orchestrating all steps required to safely
    initialise a fully operational Bank, including allocation of a valid sort
    code range and recording allocation metadata for audit purposes.

    Responsibilities:
        - Validates input parameters for bank creation
        - Creates the Bank domain entity
        - Allocates a SortCode range either from the reusable pool or by
          requesting a new allocation block
        - Persists the assigned range to the SortCode model
        - Records allocation decisions for auditing and traceability

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

    @staticmethod
    def create_bank(*, name: str, description: str, branch_name: str) -> Bank:
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
        if not (all([isinstance(param, str) for param in (name, description, branch_name)])):
            raise ValueError(_("One or more of the values is not a string",
                               f"name has type: {type(name).__name__}",
                               f"description has type: {type(description).__name__}",
                                f"branch_name has type: {type(branch_name).__name__}",
                               ))
        
        reassigned = False
        msg        = None

        with transaction.atomic():
        
            bank = Bank(
                name=name,
                description=description,
                branch_name=branch_name,
                bank_code = name[0:2] + generate_secure_code(),
            )
            bank.save()
            sortcode_block = SortCodeRangePool.get_available()

            if sortcode_block:
                reassigned  = True
                msg         = "Reassigned a sortcode block"

                sortcode_block.is_claimed = True
                sortcode_block.claimed_by = bank
                sortcode_block.save()
            else:
                sortcode_block = SortCodeAllocationState.allocate_next_range()

            if not (sortcode_block):
                raise ValueError(_("Expected a sortcode range but got nothing"))
        
            
            # add the block range for each bank
            SortCode.objects.create(bank=bank, 
                    block_start=sortcode_block.start_range,
                    block_end=sortcode_block.end_range)
            
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
                sort_code = (
                    SortCode.objects
                    .select_for_update()
                    .get(bank=bank)
                )
            except SortCode.DoesNotExist:
                raise ValueError(_("No sort code found for this bank"))

            sort_code = sort_code.generate_sort_code()

            bank_account = BankAccount(
                sort_code=sort_code,
                account_number=str(
                    sort_code.last_issued_sortcode_number
                ).zfill(8),
                account_type=account_type,
            )

            if user_profile:
                bank_account.user_profile = user_profile
            
            bank_account.save()
            return bank_account   