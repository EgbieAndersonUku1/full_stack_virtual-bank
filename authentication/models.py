from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

# Create your models here.

class BaseUser(BaseUserManager):

    def create_user(self, username, email, password = None, **extra_fields):

        self._validate_user_details(username, email)

        email = self.normalize_email(email)
        user  = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True),
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("is_staff must be set to True"))
        if not extra_fields.get("is_admin"):
            raise ValueError(_("is_admin must be set to True"))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("is_superuser must be set to True"))
        if not extra_fields.get("is_active"):
            raise ValueError(_("is_active must be set to True"))
        
        return self.create_user(username, email, password, **extra_fields)

    def _validate_user_details(self, username, email):
        """"""
        if not username:
            raise ValueError(_("The username cannot be blank"))
        if not email:
            raise ValueError(_("The email cannot be blank"))
    




class User(AbstractBaseUser, PermissionsMixin):

    username     = models.CharField(_("username"), unique=True, max_length=80)
    email        = models.EmailField(_("email"), unique=True, max_length=200)
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    is_admin     = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_on   = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
  
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    objects = BaseUser()