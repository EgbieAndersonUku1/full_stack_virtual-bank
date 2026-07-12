from django.contrib import admin
from django.utils.translation import gettext_lazy as _



class StatusFilteredAdmin(admin.ModelAdmin):
    """
    Base admin class for status-specific proxy model admins.

    Filters the admin queryset by a predefined required status, allowing
    proxy admins to display only records matching their assigned status.
    
    Example:
        class PendingApplicationAdmin(StatusFilteredAdmin):
            required_status = CardRequestApplication.Status.PENDING
    """

    required_status = None

    def get_queryset(self, request):
        if self.required_status is None:
            raise ValueError(_("required_status must be defined"))

        return super().get_queryset(request).filter(
            status=self.required_status
        )