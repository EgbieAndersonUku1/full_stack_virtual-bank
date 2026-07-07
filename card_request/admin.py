from django.contrib import admin


from .models import CardRequestAgreement


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


admin.site.register(CardRequestAgreement, CardRequestAgreementAdmin)