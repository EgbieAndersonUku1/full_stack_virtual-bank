from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from django.utils.html import format_html
from .models import User


class UserInline(admin.TabularInline):
    model = Group.user_set.through
    extra = 0
    verbose_name = "User"
    verbose_name_plural = "Users"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            qs = User.get_all_users()

            if not request.user.is_superuser:
                # Since in some case depending on the permission given staff can assign other staff
                # in that case they should only see staff + normal users i.e. active accounts
                # and not locked accounts. This prevents them from assigning an inactive user or a locked account
                qs = qs.filter(is_staff=True, is_locked=False)
            else:
                qs = qs.filter(is_staff=False)
            
            qs = qs.order_by("email")
            kwargs["queryset"] = qs

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

    
class CustomGroupAdmin(GroupAdmin):
    inlines       = [UserInline]
    search_fields = ["name", "user_set__email"]
    list_filter   = ["permissions"]
    list_display = [
        "name",
        "user_count",
        "permission_count",
        "users_list",
        "last_activity",
        "role_status",
    ]

    filter_horizontal = ["permissions"]

    def user_count(self, obj):
        return obj.user_set.count()

    def permission_count(self, obj):
        return obj.permissions.count()

    def users_list(self, obj):

        users = obj.user_set.all()[:5]

        return format_html(
            ", ".join([
                f'<a href="/admin/authentication/user/{user.id}/change/">{user.username}</a>'
                for user in users
            ])
        )

    def last_activity(self, obj):
        last = obj.user_set.order_by("-last_login").first()
        return last.last_login if last else "-"

    @admin.display(description="Status")
    def role_status(self, obj):
        count = obj.user_set.count() # The number of people assigned that role

        if count == 0:
            return "⚪ Empty"
        elif count < 5:
            return "🟢 Small Role"
        elif count < 20:
            return "🟡 Medium Role"
        return "🔴 Large Role"

    
    last_activity.short_description = "Last login"
    user_count.short_description = "Users"
    permission_count.short_description = "Permissions"
    users_list.short_description = "Members Preview"


# override at import time
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)