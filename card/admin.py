from django.contrib import admin
from django.http import HttpRequest


from card.models import BankCard, CardDashboard

# Register your models here.




class BankCardAdmin(admin.ModelAdmin):
    list_display       = ["full_name", "masked_card_number", "show_in_dashboard",
                          "card_brand", "expiry_date", "created_on", "last_modified_on"]
    list_per_page      = 25
    readonly_fields    = ["id",
                          "expiry_date",
                          "created_on",
                          "last_modified_on",
                          "bank_account",
                          "card_number",
                          "card_brand",
                          "card_category",
                          "card_type",
                          "masked_card_number",
                          "full_name",
                          "default_card",
                          ]
    list_display_links = ["full_name", "masked_card_number"]

    @admin.display(description="Masked card number")
    def masked_card_number(self, obj):
        return obj.mask_card_number

    fieldsets = [
        (
            "Card Identity",
            {
                "description": (
                    "Defines the core identity of the bank card, including the "
                    "cardholder name, card number, and associated bank account."
                ),
                "fields": [
                    "id",
                    "full_name",
                    "masked_card_number",
                    "bank_account",
                ],
            },
        ),
        (
            "Card Details",
            {
                "description": (
                    "Defines the characteristics of the card, including its "
                    "brand, category, and type."
                ),
                "fields": [
                    "is_active",
                    "show_in_dashboard",
                    "default_card",
                    "card_brand",
                    "card_category",
                    "card_type",
                ],
            },
        ),
        (
            "Financial Information",
            {
                "description": (
                    "Defines financial attributes associated with the card, "
                    "including current balance and expiry information."
                ),
                "fields": [
                    "expiry_date",
                ],
            },
        ),
        (
            "Audit Information",
            {
                "description": (
                    "Tracks when the card record was created and when it was "
                    "last modified."
                ),
                "fields": [
                    "created_on",
                    "last_modified_on",
                ],
            },
        ),
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False



class CardDashboardAdmin(admin.ModelAdmin):
    list_display       = ["id", "bank_account", "max_cards_to_show",  "created_on", "last_modified_on"]
    list_per_page      = 25
    readonly_fields    = ["id", "bank_account",  "created_on", "last_modified_on"]
    list_display_links = ["id", "bank_account"]

    fieldsets = (
        (
            "Dashboard Information",
            {
                "description": (
                    "Displays the bank account associated with the dashboard "
                    "and the maximum number of cards that can be displayed."
                ),
                "fields": [
                    "id",
                    "bank_account",
                    "max_cards_to_show",
                ],
            },
        ),
        (
            "Audit Information",
            {
                "description": (
                    "Tracks when the dashboard record was created and when it "
                    "was last modified."
                ),
                "fields": [
                    "created_on",
                    "last_modified_on",
                ],
            },
        ),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False



admin.site.register(BankCard, BankCardAdmin)
admin.site.register(CardDashboard, CardDashboardAdmin)
