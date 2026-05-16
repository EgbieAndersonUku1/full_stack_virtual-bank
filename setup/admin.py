from django.contrib import admin

from .models import Pin


# Register your models here.
class PinModelAdmin(admin.ModelAdmin):

    readonly_fields    = ["id", "user", "username", "pin", "created_on", "last_updated"]
    list_display       = ["id", "username", "pin", "created_on", "last_updated"]
    list_display_links = ["id", "pin"]
    list_per_page      = 25
    list_filter        = ["is_active"]
    search_fields      = ["user__username", "user__email"]

    fieldsets = [
        (
            "Pin details",
            {
                "description": (
                    "View the securely stored PIN information linked "
                    "to the account holder. PIN values are hashed and "
                    "cannot be viewed in plain text."
                ),
                "fields": ["pin", "user", "username"]
            }
        ),

        (
            "Status",
            {
                "description": (
                    "Control the operational state of the PIN. "
                    "Inactive PINs cannot be used for authentication "
                    "or transaction verification."
                ),
                "fields": ["is_active"]
            }
        ),

        (
            "Audit",
            {
                "description": (
                    "System-generated timestamps used for auditing, "
                    "security tracking, and administrative monitoring."
                ),
                "fields": ["created_on", "last_updated"]
            }
        ),
    ]

    
    def username(self, obj):
        return obj.username


admin.site.register(Pin, PinModelAdmin)