from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from utils.admin.filter import StatusFilteredAdmin

from .models import (CardRequestAgreement, CardRequestApplication,
                     CardRequestApplicationAccepted,
                     CardRequestApplicationCancelled,
                     CardRequestApplicationLog, CardRequestApplicationPending,
                     CardRequestApplicationRejected,
                     CardRequestApplicationWithdrawn,
                     CardRequestBasicInformation,
                     CardRequestEmploymentInformation)

# Register your models here.


class CardRequestBasicInformationInline(admin.StackedInline):
    model           = CardRequestBasicInformation
    extra           = 0
    max_num         = 1
    can_delete      = False
    readonly_fields = [
        "first_name",
        "last_name",
        "full_name",
        "email",
        "phone_number",
        "address1",
        "address2",
        "city",
        "state",
        "country",
        "postal_code",
        "full_address",
        "card_type",
        "card",
        "card_brand",
        "special_requests",
        "created_on",
        "last_modified_on",
    ]


class CardRequestEmploymentInformationInline(admin.StackedInline):
    model = CardRequestEmploymentInformation
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = [
        "employer_name",
        "employment_status",
        "employment_type",
        "contract_type",
        "years_of_employment",
        "annual_income_range",
        "pay_frequency",
        "created_on",
        "last_modified_on",
    ]


class CardRequestAgreementAdmin(admin.ModelAdmin):

    list_display = ["id", "title", "created_on", "last_modified_on"]
    list_display_links = ["title"]
    readonly_fields = ["created_on", "last_modified_on"]

    fieldsets = [
        (
            "General",
            {
                "description": (
                    "Provide the agreement title and the terms and conditions "
                    "that applicants must review and accept before submitting "
                    "their card request."
                ),
                "fields": ["title", "terms_of_condition"],
            },
        ),
        (
            "Audit",
            {
                "description": (
                    "Displays automatically managed timestamps indicating when "
                    "this agreement was created and last updated."
                ),
                "fields": ["created_on", "last_modified_on"],
            },
        ),
    ]


class CardRequestApplicationBaseAdmin(admin.ModelAdmin):
    """"""

    list_display       = ["id", "user", "status", "submitted_on",
                          "reviewed_by", "created_on", "last_modified_on",

                          ]
    list_display_links = ["id", "user"]
    list_filter        = ["created_on", "submitted_on"]
    search_fields      = ["user__username", "user__email", "reviewed_by"]
    readonly_fields    = ["created_on", "last_modified_on", "user", "reviewed_by", "submitted_on", "reviewed_on",
                          "application_id"

                          ]

    inlines = [CardRequestBasicInformationInline, CardRequestEmploymentInformationInline]

    fieldsets = [
        (
            "Application Details",
            {
                "description": (
                    "Displays the applicant and the current status of their "
                    "card request application."
                ),
                "fields": ["application_id", "user", "status", "submitted_on"],
            },
        ),
        (
            "Review Information",
            {
                "description": (
                    "Contains details about the application review process, "
                    "including reviewer notes and the person responsible "
                    "for reviewing the application."
                ),
                "fields": ["reviewed_by", "reviewed_on", "notes"],
            },
        ),
        (
            "Audit",
            {
                "description": (
                    "Displays automatically managed timestamps indicating when "
                    "this application was created and last updated."
                ),
                "fields": ["created_on", "last_modified_on"],
            },
        ),


    ]

    def has_add_permission(self, request):
        return False


class CardRequestApplicationAdmin(CardRequestApplicationBaseAdmin):
    list_filter  = ["status", "created_on", "submitted_on"]



class CardRequestApplicationLogAdmin(admin.ModelAdmin):

    list_display       = ["id",  "username", "action", "email", "created_on"]
    list_display_links = ["id", "username"]
    list_filter        = ["action", "created_on"]
    search_fields      = ["username", "email", "full_name", "notes"]
    readonly_fields    = ["user", "username", "email", "full_name",
                          "action", "notes", "created_on", "last_modified_on",
                          ]

    fieldsets = [
        (
            "Log Information",
            {
                "description": (
                    "Displays the recorded audit information for a card request "
                    "application event. Log entries provide a historical record "
                    "of actions performed within the card request workflow."
                ),
                "fields": [
                    "action",
                    "notes",
                ],
            },
        ),
        (
            "User Snapshot",
            {
                "description": (
                    "Displays the user details captured at the time the log "
                    "entry was created. These values remain unchanged even if "
                    "the user's account information is later updated or deleted."
                ),
                "fields": [
                    "user",
                    "username",
                    "full_name",
                    "email",
                ],
            },
        ),
        (
            "Audit",
            {
                "description": (
                    "Displays automatically managed timestamps indicating when "
                    "this log entry was created and last updated."
                ),
                "fields": [
                    "created_on",
                    "last_modified_on",
                ],
            },
        ),
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False




class CardRequestApplicationPendingAdmin(CardRequestApplicationBaseAdmin, StatusFilteredAdmin):
    """
    Admin configuration for the pending card request application proxy.

    Filters records to display only applications with a pending status.
    """

    required_status = CardRequestApplication.Status.PENDING


class CardRequestApplicationAcceptedAdmin(CardRequestApplicationBaseAdmin, StatusFilteredAdmin):
    """
    Admin configuration for the accepted card request application proxy.

    Filters records to display only applications with an accepted status.
    """

    required_status = CardRequestApplication.Status.ACCEPTED


class CardRequestApplicationWithdrawnAdmin(CardRequestApplicationBaseAdmin, StatusFilteredAdmin):
    """
    Admin configuration for the withdrawn card request application proxy.

    Filters records to display only applications with a withdrawn status.
    """

    required_status = CardRequestApplication.Status.WITHDRAWN


class CardRequestApplicationRejectedAdmin(CardRequestApplicationBaseAdmin, StatusFilteredAdmin):
    """
    Admin configuration for the rejected card request application proxy.

    Filters records to display only applications with a rejected status.
    """

    required_status = CardRequestApplication.Status.REJECTED


class CardRequestApplicationCancelledAdmin(CardRequestApplicationBaseAdmin, StatusFilteredAdmin):
    """
    Admin configuration for the cancelled card request application proxy.

    Filters records to display only applications with a cancelled status.
    """

    required_status = CardRequestApplication.Status.CANCELLED




admin.site.register(CardRequestAgreement, CardRequestAgreementAdmin)
admin.site.register(CardRequestApplication, CardRequestApplicationAdmin)
admin.site.register(CardRequestApplicationPending, CardRequestApplicationPendingAdmin)
admin.site.register(CardRequestApplicationAccepted, CardRequestApplicationAcceptedAdmin)
admin.site.register(CardRequestApplicationWithdrawn,CardRequestApplicationWithdrawnAdmin)
admin.site.register(CardRequestApplicationRejected, CardRequestApplicationRejectedAdmin)
admin.site.register(CardRequestApplicationCancelled, CardRequestApplicationCancelledAdmin)
admin.site.register(CardRequestApplicationLog, CardRequestApplicationLogAdmin)
