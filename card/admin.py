from django.contrib import admin

from bank.models import BankAccount
from card.models import BankCard

# Register your models here.




class BankCardAdmin(admin.ModelAdmin):
    list_display       = ["id", "full_name", "masked_card_number",
                          "card_brand", "expiry_date", "created_on", "last_modified_on"]
    list_per_page      = 25
    readonly_fields    = ["id",
                          "expiry_date",
                          "created_on",
                          "last_modified_on",
                          "balance",
                          "bank_account",
                          "card_number",
                          "card_brand",
                          "card_category",
                          "card_type",
                          "masked_card_number",
                          "full_name",
                          ]
    list_display_links = ["id", "full_name"]

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
                    "balance",
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





admin.site.register(BankCard, BankCardAdmin)
