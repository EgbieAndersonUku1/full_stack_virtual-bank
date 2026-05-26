from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import FileExtensionValidator

from django.contrib.auth import get_user_model



User = get_user_model()

# Create your models here.

class UserProfile(models.Model):
    
    class Gender(models.TextChoices):
        MALE              = "Male", _("Male")
        FEMALE            = "Female", _("Female")
        PREFER_NOT_TO_SAY = "Prefer_not_to_say", _("Prefer not to say")

    first_name     = models.CharField(max_length=20)
    last_name      = models.CharField(max_length=20)
    middle_name    = models.CharField(max_length=20, null=True, blank=True)
    gender         = models.CharField(max_length=20, choices=Gender.choices, default=Gender.PREFER_NOT_TO_SAY)
    bio            = models.TextField(max_length=150, null=True)
    email          = models.CharField(max_length=300, blank=True, null=True)
    phone_number   = PhoneNumberField(unique=True, blank=True, null=True, max_length=20)
    profile_pic    = models.FileField(upload_to="profile/pic/", null=True, blank=True,
                            validators=[FileExtensionValidator(["png", "jpg", "jpeg", "svg"])]
                           )
    city           = models.CharField(max_length=40)
    address_line_1 = models.CharField(max_length=200, blank=True, null=True)
    address_line_2 = models.CharField(max_length=200, blank=True, null=True)
    postcode      = models.CharField(max_length=10)
    country        = CountryField(blank_label="(select country)")
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", editable=False, blank=True, null=True)
    created_on     = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_updated   = models.DateTimeField(auto_now=True)


    @classmethod
    def get_profile_by_user(cls, user: User) -> UserProfile | None:

        if not isinstance(user, User):
            raise TypeError(_(f"Expected a user instance, but got a user with type ({type(user).__name__})"))
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None

    @property
    def profile_img(self):
        return self.profile_pic.url
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} is from {self.country}"
    