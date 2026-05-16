from django.contrib import admin
from django.db.models import Count
from django.db import models


from .models import (Bank, 
                     BankAccount, 
                     SortCode, 
                     SortCodeAllocationState, 
                     SortCodeAllocatorLastRecordLookup,
                     SortCodeRangePool, 
                     SortCodeAllocationStateLog
                     )


# Register your models here.


class BankAdmin(admin.ModelAdmin):

    readonly_fields     = ["last_activity_at", "bank_code", "created_on", "last_updated", 
                            "bank_accounts_count", "interest_rate_bps", "id"]
    list_display        = ["name", "bank_code", "bank_accounts_count", "branch_name", "country", "phone_number", "created_on"]
    list_display_links  = ["bank_code", "name"]
    list_filter         = ["branch_name", "country", "bank_code", "name"]
    ordering            = [ "-created_on"]
   
    fieldsets = [(
             "Bank Identity",
                {
                "description": (
                    "Defines the core identity and branding information for the bank, "
                    "including its unique bank code, public description, and logo."
                ),
                "fields": [
                    "id",
                    "bank_code",
                    "name",
                    "description",
                    "logo",
                ],
            },
        ),

        (
            "Branch & Location",
            {
                "description": (
                    "Stores the primary branch and geographic location details associated "
                    "with the bank."
                ),
                "fields": [
                    "branch_name",
                    "address_line_1",
                    "address_line_2",
                    "post_code",
                    "country",
                ],
            },
        ),

        (
            "Contact Details",
            {
                "description": (
                    "Contains official contact information used for communication and operational purposes."
                ),
                "fields": [
                    "phone_number",
                ],
            },
        ),

        (
            "Banking Products & Services",
            {
                "description": (
                    "Controls the banking products and account services offered by this bank."
                ),
                "fields": [
                    "offer_overdraft",
                    "offer_saving_account",
                    "offer_loans",
                ],
            },
        ),

        (
            "Financial Settings",
            {
                "description": (
                    "Defines financial configuration settings, including interest behaviour, "
                    "deposit requirements, and bank account capacity metrics."
                ),
                "fields": [
                    "interest_period",
                    "interest_rate",
                    "interest_rate_bps",
                    "minimum_opening_deposit",
                    "monthly_deposit",
                    "bank_accounts_count",
                ],
            },
        ),

        (
            "System & Audit",
            {
                "description": (
                    "Displays system-generated audit information and lifecycle metadata "
                    "for this bank record."
                ),
                "fields": [
                    "created_on",
                    "last_updated",
                    "last_activity_at",
                ],
            },
        ),
    ]
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.annotate(
            total_bank_accounts=Count(
                "sort_codes__bank_accounts",
                distinct=True
            )
        )

    @admin.display(description="Number of bank accounts")
    def bank_accounts_count(self, obj):
        return obj.bank_accounts_count

    def has_add_permission(self, request):
        return False




class BankAccountAdmin(admin.ModelAdmin):
    readonly_fields   = ["sort_code", "account_number",  "user_profile", "bank_name",
                         "balance", "last_interest_run", "account_type", "status", "interest_enabled", "created_on", "last_updated"]
    list_display       = ["id", "bank_name", "user_profile", "sort_code", "account_number", 
                         "balance", "last_interest_run", "account_type", "status", "created_on"]
    list_display_links = ["id", "sort_code", "bank_name", "account_number"]
    list_filter        = ["status", "account_type", "interest_enabled", "sort_code__bank",]
    search_fields      = ["account_number", "sort_code__external_sort_code", "sort_code__bank__name"]
    search_help_text   =  ("Search by bank name, account number, or sort code. "
                           "Bank name searches are prioritised."
                        )
    list_per_page      =  20
    ordering           = [ "-created_on"]
    

    fieldsets = [(
            "Bank Details",
            {
                "description": (
                    "Displays the core banking information associated with this account, "
                    "including account identifiers, balance information, and account configuration settings."
                ),
                "fields": [
                    "bank_name",
                    "account_type",
                    "sort_code",
                    "account_number",
                    "balance",
                    "interest_enabled",
                ],
            },
        ),

        (
            "User Profile",
            {
                "description": (
                    "Identifies the customer profile linked to this bank account."
                ),
                "fields": [
                    "user_profile",
                ],
            },
        ),

        (
            "System & Audit",
            {
                "description": (
                    "Displays system-generated timestamps and audit metadata for this bank account record."
                ),
                "fields": [
                    "created_on",
                    "last_updated",
                    "last_interest_run",
                ],
            },
        ),
    ]

    @admin.display(ordering="sort_code__bank__name", description="Bank")
    def bank_name(self, obj):
        return obj.sort_code.bank.name
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    

class SortCodeAllocationStateAdmin(admin.ModelAdmin):
    readonly_fields = ["id",
                       "formatted_block_start", 
                       "formatted_block_end", 
                       "total_sortcode_capacity",
                        "total_sortcode_issued",
                        "remaining_sortcodes",
                        "allocation_utilisation_percent",
                        "bank",
                        "block_size",
                        "start_range",
                        "end_range",
                         "last_issued_sortcode_number", 
                        "external_sortcode",
                         "last_created_account",
                         "number_of_sortcode_used",
                         "created_on"
                        ]
    list_per_page       = 25
    list_display        = [ "id", "bank",  "block_size", "start_range", "end_range", 
                          "external_sortcode","last_created_account", "created_on"
                          ]
    search_fields      = ["bank__name", "bank__bank_code"]
    ordering           = [ "-created_on"]
    list_display_links = ["id", "bank", "external_sortcode"]
    fieldsets          = [("Bank Information", { "description": (
                                "Displays the bank associated with this allocation state and the "
                                "total sort code capacity assigned to its allocated block."
                            ),"fields": [ "bank", "total_sortcode_capacity",]}),
                    ("Allocated Block Range", {
                        "description": (
                                "Represents the globally allocated sequential "
                                "sort code range reserved for this bank."
                            ),
                            "fields": ["formatted_block_start", "formatted_block_end"],
                     },
                    ),

                    ("Allocation Progress", {
                            "description": (
                                "Monitors allocation progress and utilisation for the bank’s assigned sort code block"
                            ),
                            "fields": [
                                    "external_sortcode",
                                    "last_created_account",
                                    "number_of_sortcode_used",
                                    "remaining_sortcodes",
                                    "allocation_utilisation_percent",
                                ],
                        },
                    ),

                      ("System & Audit", {
                           "description": (
                                    "Displays system-generated audit information and lifecycle metadata "
                                    "for this allocation record."
                             ),
                            "fields": [
                                   "created_on",
                                   "last_updated",
                                ],
                        },
                    ),

                    
                ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
    @admin.display(description="Total Capacity")
    def total_sortcode_capacity(self, obj):
        return obj.total_sortcode_capacity

    @admin.display(description="Total Issued")
    def total_sortcode_issued(self, obj):
        return obj.issued_sortcodes_count

    @admin.display(description="Remaining")
    def remaining_sortcodes(self, obj):
        return obj.remaining_sortcodes

    @admin.display(description="Utilisation (%)")
    def allocation_utilisation_percent(self, obj):
        return obj.allocation_utilisation_percent

    @admin.display(description="Block Start")
    def formatted_block_start(self, obj):
        return f"{obj.start_range:,}"

    @admin.display(description="Block End")
    def formatted_block_end(self, obj):
        return f"{obj.end_range:,}"
    
    @admin.display(description="Sortcodes used so far")
    def number_of_sortcode_used(self, obj):
        return obj.issued_sortcodes_count
    
    @admin.display(description="Last issued external sortcode")
    def external_sortcode(self, obj):
        return obj.external_sortcode
    
    @admin.display(description="Last issued account number")
    def last_created_account(self, obj):
        return obj.account_number
    


class SortCodeAllocatorRecordLookupAdmin(admin.ModelAdmin):
    readonly_fields = ["block_size", "start_range", "end_range", "created_on", "last_updated"]
    list_display    = ["block_size", "start_range", "end_range", "created_on", "last_updated"]
    list_per_page   = 1
    fieldsets       = [(
            "Global Allocation State",
            {
                "description": (
                    "Tracks the most recently allocated global sort code block range used "
                    "for sequential bank allocation across the system."
                ),
                "fields": [
                    "block_size",
                    "start_range",
                    "end_range",
                ],
            },
        ),

        (
            "System & Audit",
            {
                "description": (
                    "Displays system-generated audit information and lifecycle metadata "
                    "for this allocation lookup record."
                ),
                "fields": [
                    "created_on",
                    "last_updated",
                ],
            },
        ),
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class SortCodeAdmin(admin.ModelAdmin):
    readonly_fields    = [ "id", "external_sort_code",  "created_on", "last_updated",  "bank"]
    list_display       = ["id", "bank", "external_sort_code", "created_on", "last_updated"]
    list_display_links = ["id", "bank", "external_sort_code"]
    list_filter        = ["bank"]
    search_fields      = ["external_sort_code"]
    search_help_text   =  ("Search by by external sortcode")
    ordering           = [ "-created_on"]
    fieldsets = [(
            "Bank Issued To",
            {
                "description": (
                    "Displays the bank associated with and authorised to use this issued sort code."
                ),
                "fields": [
                    "bank",
                ],
            },
        ),

        (
            "Sort Code",
            {
                "description": (
                    "Displays the externally formatted sort code assigned to the bank."
                ),
                "fields": [
                    "external_sort_code",
                ],
            },
        ),

        (
            "System & Audit",
            {
                "description": (
                    "Displays system-generated audit information and lifecycle metadata "
                    "for this sort code record."
                ),
                "fields": [
                    "created_on",
                    "last_updated",
                ],
            },
        ),
    ]
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False



class SortCodeRangePoolAdmin(admin.ModelAdmin):

    readonly_fields    = [ "id", "start_range", "end_range","created_on", "last_updated", "claimed_on", "claimed_by"]
    list_display       = [ "id",  "start_range", "end_range", "is_claimed", "claimed_by", "claimed_on","created_on"]
    list_display_links = [ "id","start_range", "end_range"]
    list_filter        = [ "is_claimed", "created_on", "claimed_on", "claimed_by"]
    search_fields      = [ "start_range", "end_range","claimed_by__name","claimed_by__bank_code"]
    ordering           = [ "-created_on"]
    list_per_page      = 20
    fieldsets = [

        (
            "Range Allocation Block",
            {
                "description": (
                    "Represents a reserved global sort code allocation block available "
                    "for assignment or already claimed by a bank."
                ),
                "fields": [
                    "start_range",
                    "end_range",
                    "is_claimed",
                ],
            },
        ),

        (
            "Claim Information",
            {
                "description": (
                    "Tracks whether the allocation block has been claimed and identifies "
                    "the bank currently associated with the range."
                ),
                "fields": [
                    "claimed_by",
                    "claimed_on",
                ],
            },
        ),

        (
            "System & Audit",
            {
                "description": (
                    "Displays system-generated audit information and lifecycle metadata "
                    "for this allocation pool record."
                ),
                "fields": [
                    "created_on",
                    "last_updated",
                ],
            },
        ),
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class SortCodeAllocationStateLogAdmin(admin.ModelAdmin):

    readonly_fields    = ["assigned_to", "description", "start_range", "end_range", "created_on", "last_updated"]
    list_display       = ["id","assigned_to", "start_range", "end_range", "created_on"]
    ordering           = ["-created_on"]
    list_display_links = [ "id","assigned_to"]
    list_filter        = ["assigned_to",]
    search_fields      = ["assigned_to__name", "assigned_to__bank_code", "start_range","end_range"]
    list_per_page      = 20

    fieldsets = [

        (
            "Allocation Event",
            {
                "description": (
                    "Records the bank associated with this allocation event and "
                    "provides descriptive operational context for the action performed."
                ),
                "fields": [
                    "assigned_to",
                    "description",
                ],
            },
        ),

        (
            "Allocated Range Details",
            {
                "description": (
                    "Displays the sort code range boundaries assigned during "
                    "this allocation operation."
                ),
                "fields": [
                    "start_range",
                    "end_range",
                ],
            },
        ),

        (
            "System & Audit",
            {
                "description": (
                    "Displays system-generated audit information and lifecycle metadata "
                    "for this allocation log record."
                ),
                "fields": [
                    "created_on",
                    "last_updated",
                ],
            },
        ),
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False




admin.site.register(Bank, BankAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(SortCode, SortCodeAdmin)
admin.site.register(SortCodeAllocatorLastRecordLookup, SortCodeAllocatorRecordLookupAdmin)
admin.site.register(SortCodeAllocationState, SortCodeAllocationStateAdmin)
admin.site.register(SortCodeRangePool, SortCodeRangePoolAdmin)
admin.site.register(SortCodeAllocationStateLog, SortCodeAllocationStateLogAdmin)


