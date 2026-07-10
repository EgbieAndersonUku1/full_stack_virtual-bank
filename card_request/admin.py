from django.contrib import admin


from .models import CardRequestAgreement, CardRequestApplication, CardRequestApplicationLog, CardRequestBasicInformation, CardRequestEmploymentInformation


# Register your models here.

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

    

class CardRequestApplicationAdmin(admin.ModelAdmin):

    list_display       = ["id", "user", "status", "submitted_on", "reviewed_by", "created_on", "last_modified_on"]
    list_display_links = ["id", "user"]
    list_filter        = ["status", "created_on", "submitted_on"]
    search_fields      = ["user__username", "user__email", "reviewed_by"]
    readonly_fields    = ["created_on", "last_modified_on", "user", "reviewed_by", "submitted_on", "reviewed_on"]

    fieldsets = [
        (
            "Application Details",
            {
                "description": (
                    "Displays the applicant and the current status of their "
                    "card request application."
                ),
                "fields": ["user", "status", "submitted_on"],
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
    
  
    

class CardRequestBasicInformationAdmin(admin.ModelAdmin):

    list_display       = ["id", "full_name", "email", "card_type", "card", "card_brand", "created_on"]
    list_display_links = ["id", "full_name"]
    list_filter        = ["card_type", "card", "card_brand", "country", "created_on"]
    search_fields      = ["first_name", "last_name", "email", "phone_number", "application__user__username"]
    readonly_fields    = ["created_on", "last_modified_on", "full_name", "get_full_address", "application"]
    fieldsets           = [
        (
             "Applicant Information",
            {
                "description": (
                    "Displays the personal details provided by the applicant "
                    "when submitting their card request."
                ),
                    "fields": [
                        "application",
                        "first_name",
                        "last_name",
                        "full_name",
                        "email",
                        "phone_number",
                    ],
                },
        ),
        (
            "Address Information",
            {
                "description": (
                    "Displays the applicant's provided address details "
                    "associated with the card request."
                ),
                "fields": ["address1", "address2", "city", "state", "country", "postal_code", "get_full_address"],
            },
        ),
        (
            "Card Preferences",
            {
                "description": (
                    "Displays the requested card type, card category, and "
                    "preferred card brand selected by the applicant."
                ),
                "fields": ["card_type", "card", "card_brand"],
            },
        ),
        (
            "Additional Requests",
            {
                "description": (
                    "Contains any additional instructions or special requests "
                    "provided by the applicant."
                ),
                "fields": [ "special_requests"],
            },
        ),
        (
            "Audit",
            {
                "description": (
                    "Displays automatically managed timestamps indicating when "
                    "this information was created and last updated."
                ),
                "fields": ["created_on", "last_modified_on"],
            },
        ),
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False



class CardRequestEmploymentInformationAdmin(admin.ModelAdmin):

    list_display = ["id", "application", "employment_status", "employment_type", "annual_income_range", "created_on"]
    list_display_links = ["id", "application"]
    list_filter        = ["employment_status", "employment_type", "years_of_employment", "annual_income_range",
                          "pay_frequency",
                          "created_on",
                          ]

    search_fields   = ["employer_name", "application__user__username", "card_request__user__email"]
    readonly_fields = ["created_on", "last_modified_on", "application"]
    fieldsets       = [
        (
            "Application Information",
            {
                "description": (
                    "Displays the card request application associated with "
                    "this employment information."
                ),
                "fields": [
                    "application",
                ],
            },
        ),
        (
            "Employment Details",
            {
                "description": (
                    "Contains employment information provided by the applicant, "
                    "including employment status, type, and duration."
                ),
                "fields": ["employer_name", "employment_status", "employment_type", "contract_type",
                           "years_of_employment",
                         ],
            },
        ),
        (
            "Income Information",
            {
                "description": (
                    "Displays the applicant's income range and payment "
                    "frequency details."
                ),
                "fields": ["annual_income_range", "pay_frequency"],
            },
        ),
        (
            "Audit",
            {
                "description": (
                    "Displays automatically managed timestamps indicating when "
                    "this employment information was created and last updated."
                ),
                "fields": ["created_on", "last_modified_on"],
            },
        ),
    ]   
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False



class CardRequestApplicationLogAdmin(admin.ModelAdmin):

    list_display       = ["id", "action", "username", "email", "created_on"]
    list_display_links = ["id", "username"]
    list_filter        = ["action", "created_on"]
    search_fields      = ["username", "email", "full_name", "notes"]
    readonly_fields    = ["user", "username", "email", "full_name", "action", "notes", "created_on", "last_modified_on"]

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
     
    
admin.site.register(CardRequestAgreement, CardRequestAgreementAdmin)
admin.site.register(CardRequestApplication, CardRequestApplicationAdmin)
admin.site.register(CardRequestBasicInformation, CardRequestBasicInformationAdmin)
admin.site.register(CardRequestEmploymentInformation, CardRequestEmploymentInformationAdmin)
admin.site.register(CardRequestApplicationLog, CardRequestApplicationLogAdmin)