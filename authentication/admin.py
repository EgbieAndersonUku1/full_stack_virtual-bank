from django.contrib import admin

from .models import User


# Register your models here.
class UserAdminModel(admin.ModelAdmin):
    readonly_fields = ["created_on", "last_updated", "last_login"]
    list_display = ["id", "email", "username", "is_active", "is_staff", "is_admin", "is_superuser", "last_login"]
    list_display_links = ["id", "email", "username"]

    fieldsets = [
        (None, {"fields": ["username", "email", "is_active"]}),
        ("Permissions", {"fields": ["is_staff", "is_admin", "is_superuser"]}),
        ("Audit", {"fields": ["created_on", "last_updated", "last_login"]})
    ]


admin.site.register(User, UserAdminModel)