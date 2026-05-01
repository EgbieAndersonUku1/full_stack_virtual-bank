from django.contrib import admin

from .models import User, Verification, EmailLog


# Register your models here.
class UserAdminModel(admin.ModelAdmin):
    readonly_fields = ["created_on", "last_updated", "last_login"]
    list_display = ["id", "email", "username", "is_active", "is_staff", "is_admin", "is_superuser", "last_login"]
    list_display_links = ["id", "email", "username"]

    search_fields = ["username", "email"]
    list_per_page = 25
    list_filter   = ["is_active", "is_staff", "is_admin", "is_superuser"]


    fieldsets = [
        (None, {"fields": ["username", "email", "is_active"]}),
        ("Permissions", {"fields": ["is_staff", "is_admin", "is_superuser"]}),
        ("Audit", {"fields": ["created_on", "last_updated", "last_login"]})
    ]


class VerificationAdminModel(admin.ModelAdmin):
    readonly_fields     = ["created_on", "last_updated", "masked_code", "description", "is_used", "used_at", "expiry_date", "user"]
    list_display        = ["id", "user", "expiry_date", "is_used", "created_on", "last_updated" ]
    search_fields       = ["user", "id"]
    list_display_links  = ["id", "user"]
    list_per_page       = 25

    fieldsets = [
        ("User & Code", {
            "fields": ["user", "masked_code", "description"]
        }),
        ("Status", {
            "fields": ["is_used", "used_at"]
        }),
        ("Expiry", {
            "fields": ["expiry_date"]
        }),
        ("Audit", {
            "fields": ["created_on", "last_updated"]
        }),
    ]

    def masked_code(self, obj):
        code = obj.verification_code or ""
        return f"****{code[-3:]}" if len(code) >= 3 else "****"


class EmailLogAdminModel(admin.ModelAdmin):
    readonly_fields = ["from_email", "to_email", "subject", "status", "email_body", "created_on", "sent_at"]
    list_display    = ["from_email", "to_email", "subject", "status", "email_body", "created_on", "sent_at"]
    search_fields   = ["from_email", "to_email"]
    list_per_page   = 25



admin.site.register(User, UserAdminModel)
admin.site.register(Verification, VerificationAdminModel)
admin.site.register(EmailLog, EmailLogAdminModel)