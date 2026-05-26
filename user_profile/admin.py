from django.contrib import admin


from .models import UserProfile



class UserProfileAdmin(admin.ModelAdmin):

    readonly_fields = ["created_on", "last_updated", "user",]
    list_display  = ["first_name", "last_name", "gender", "city", "country", "phone_number", "created_on",]
    list_display_links = [ "first_name", "last_name",]
    list_filter = [ "gender",  "country", "city", "created_on" ]
    list_per_page = 25

    ordering = ["-created_on"]

    fieldsets = [

        (
            "Personal Information",
            {
                "description": (
                    "Core identity details for the user profile including name and gender."
                ),
                "fields": [
                    "first_name",
                    "middle_name",
                    "last_name",
                    "gender",
                    "bio",
                ],
            },
        ),

        (
            "Contact Information",
            {
                "description": (
                    "Contact details associated with the user profile."
                ),
                "fields": [
                    "email",
                    "phone_number",
                ],
            },
        ),

        (
            "Profile Media",
            {
                "description": (
                    "User profile media such as profile picture."
                ),
                "fields": [
                    "profile_pic",
                ],
            },
        ),

        (
            "Address Information",
            {
                "description": (
                    "Residential or location details of the user."
                ),
                "fields": [
                    "city",
                    "address_line_1",
                    "address_line_2",
                    "postcode",
                    "country",
                ],
            },
        ),

        (
            "System & Audit",
            {
                "description": (
                    "System-managed metadata for tracking profile creation and updates."
                ),
                "fields": [
                    "user",
                    "created_on",
                    "last_updated",
                ],
            },
        ),
    ]



admin.site.register(UserProfile, UserProfileAdmin)