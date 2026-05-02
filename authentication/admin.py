from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (User, Verification, 
                     EmailLog, 
                     VerificationPending, 
                     VerificationBlock,
                     VerificationUsed,
                     VerificationExpired
                     )

# Register your models here.

class BaseVerificationAdmin(admin.ModelAdmin):
    """
    Reusable base admin for Verification models.

    Defines a consistent, read-only admin interface with structured fieldsets,
    search capabilities, and masked display of sensitive data. Designed to be
    extended by proxy admins which displayed filtered verification states (e.g.
    pending, expired) without duplicating configuration. 

    Each model can extend or override a current field.
    """
    readonly_fields     = ["created_on", "last_updated", "masked_code", "verification_type", "is_used",
                            "description",  "used_at", "expiry_date", "user", "sent_at" ]
    list_display        = ["id", "user", "status", "expiry_date", "is_used", "created_on", "last_updated" ]
    search_fields       = ["id",  "user__email", "user__username"]
    list_display_links  = ["id", "user"]
    list_filter         = ["user"]
    list_per_page       = 25

    fieldsets = [
        ("User & Code", {
            "fields": ["user", "masked_code", "description", "verification_type"]
        }),
        ("Status", {
            "fields": ["is_used", "status", "num_of_resend_requests"]
        }),
        ("Expiry", {
            "fields": ["expiry_date"]
        }),
        ("Audit", {
            "fields": ["created_on", "last_updated", "sent_at", "used_at"]
        }),
    ]

    def masked_code(self, obj):
        code = obj.verification_code or ""
        return f"****{code[-3:]}" if len(code) >= 3 else "****"
    
    def has_add_permission(self, request):
        return False


class VerificationStatusAdmin(BaseVerificationAdmin):
    """
    Base admin for status-specific verification views.

    Filters the queryset by a predefined status, allowing proxy admins
    to display a focused subset of verification records.
    """
    status_filter = None

    def get_queryset(self, request):
        if self.status_filter is None:
            raise ValueError(_("status_filter must be defined"))

        return super().get_queryset(request).filter(status=self.status_filter)
    


class UserAdminModel(admin.ModelAdmin):
    readonly_fields = ["created_on", "last_updated", "last_login", "username", "email"]
    list_display = ["id", "email", "username", "is_active", "is_staff", "is_admin", "is_superuser", "last_login"]
    list_display_links = ["id", "email", "username"]

    search_fields = ["username", "email"]
    list_per_page = 25
    list_filter   = ["is_active", "is_staff", "is_admin", "is_superuser"]


    fieldsets = [
        (None, {"fields": ["username", "email", "is_active", "is_email_verified"]}),
        ("Permissions", {"fields": ["is_staff", "is_admin", "is_superuser"]}),
        ("Audit", {"fields": ["created_on", "last_updated", "last_login"]})
    ]


class VerificationAdminModel(BaseVerificationAdmin):
    """Admin view for verification records with filtering by status and usage state."""
    list_filter = ["status", "is_used"]


class VerificationBlockAdmin(VerificationStatusAdmin):
    """Admin view for verification records with BLOCKED status."""
    status_filter = Verification.Status.BLOCKED


class VerificationPendingAdmin(VerificationStatusAdmin):
    """Admin view for verification records with PENDING status."""
    status_filter = Verification.Status.PENDING


class VerificationExpiredAdmin(VerificationStatusAdmin):
    """Admin view for verification records with EXPIRED status."""
    status_filter = Verification.Status.EXPIRED


class VerificationUsedAdmin(VerificationStatusAdmin):
    """Admin view for verification records with SUCCESS status."""
    status_filter = Verification.Status.VERIFIED

   
class EmailLogAdminModel(admin.ModelAdmin):
    readonly_fields = ["from_email", "to_email", "subject", "status", "email_body", "created_on", "sent_at"]
    list_display    = ["from_email", "to_email", "subject", "status", "email_body", "created_on", "sent_at"]
    search_fields   = ["from_email", "to_email"]
    list_per_page   = 25



admin.site.register(User, UserAdminModel)
admin.site.register(Verification, VerificationAdminModel)
admin.site.register(VerificationPending, VerificationPendingAdmin)
admin.site.register(VerificationExpired, VerificationExpiredAdmin)
admin.site.register(VerificationBlock, VerificationBlockAdmin)
admin.site.register(VerificationUsed, VerificationUsedAdmin)
admin.site.register(EmailLog, EmailLogAdminModel)