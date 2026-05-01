from __future__ import annotations
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django_email_sender.models import EmailBaseLog 
from django.conf import settings



# Create your models here.

class BaseUser(BaseUserManager):

    def create_user(self, email, username, password = None, **extra_fields):

        self._validate_user_details(username, email)

        email = self.normalize_email(email)
        user  = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, username, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
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
        
        return self.create_user(email, username, password, **extra_fields)

    def _validate_user_details(self, username, email):
        """"""
        if not username:
            raise ValueError(_("The username cannot be blank"))
        if not email:
            raise ValueError(_("The email cannot be blank"))
    


class User(AbstractBaseUser, PermissionsMixin):

    username          = models.CharField(_("username"), unique=True, max_length=80)
    email             = models.EmailField(_("email"), unique=True, max_length=200)
    is_email_verified = models.BooleanField(default=False)
    is_active         = models.BooleanField(default=True)
    is_staff          = models.BooleanField(default=False)
    is_admin          = models.BooleanField(default=False)
    is_superuser      = models.BooleanField(default=False)
    created_on        = models.DateTimeField(auto_now_add=True)
    last_updated      = models.DateTimeField(auto_now=True)
  
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    objects = BaseUser()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._IS_EMAIL_VERIFIED_FLAG = "is_email_verified"

    def __str__(self):
        if self.email:
            return self.email.lower()

    def is_user_email_verified(self):
        return self.is_email_verified == True
    
    def mark_email_as_verified(self, commit: bool = True) -> User | None:
        """
        Marks the user's email as verified.

        This method updates the `is_email_verified` flag on the user instance.
        It can either immediately persist the change to the database or defer, this
        is useful if you want to perform multiple actions before saving.
     
        Args:
            commit (bool): If True, the change is immediately saved to the database.
                        If False, the change is only applied in memory and must
                        be saved manually later.

        Returns:
            User | None: Returns the updated user instance if committed, otherwise None.

        Note:
            The `commit` parameter is useful when multiple field updates are being
            performed together, allowing a single database write for efficiency.
        """
        self.is_email_verified = True
       
        if commit:
            return self._update_fields(fields=[self._IS_EMAIL_VERIFIED_FLAG])
                
    def mark_email_as_unverified(self, commit: bool = True) -> User | None:
        """
        Marks the user's email as unverified.

        This method updates the `is_email_verified` flag on the user instance.
        It can either immediately persist the change to the database or defer, this
        is useful if you want to perform multiple actions before saving.
     
        Args:
            commit (bool): If True, the change is immediately saved to the database.
                        If False, the change is only applied in memory and must
                        be saved manually later.

        Returns:
            User | None: Returns the updated user instance if committed, otherwise None.

        Note:
            The `commit` parameter is useful when multiple field updates are being
            performed together, allowing a single database write for efficiency.
        """
        self.is_email_verified = False

        if commit:
            return self._update_fields(fields=[self._IS_EMAIL_VERIFIED_FLAG])

    def _update_fields(self, fields: list):
        if not isinstance(fields, list):
            raise TypeError(_(f"Expected the fields to be list but got value with type {type(fields).__name__}"))
        self.save(update_fields=fields)
        return self

    @classmethod
    def get_by_username(cls, username: str) -> User | None:
        """"""
        return cls._get_value(field_value=username, field_name="username")

    @classmethod
    def get_by_email(cls, email: str) -> User | None:
        """"""
        return cls._get_value(field_value=email, field_name="email")

    @classmethod
    def _get_value(cls, field_value: str, field_name: str ="username") -> User | None:
        """"""
        if not (isinstance(field_value, str) and isinstance(field_name, str)):
            raise TypeError(_("The field value and field name must be string. Got type {} for field value and got type for field name".format(type(field_value), type(field_name))))
        try:
            field_value = field_value.lower()
            if field_name == "username":
                return cls.objects.get(username=field_value)
            return cls.objects.get(email=field_value)
        except cls.DoesNotExist:
            return None
        
    def save(self, *args, **kwargs):

        if self.email:
            self.email = self.email.lower().strip()

        if self.username:
            self.username = self.username.lower().strip()

        super().save(*args, **kwargs)
        

class Verification(models.Model):

    user                  = models.ForeignKey(User, on_delete=models.CASCADE)
    verification_code     = models.CharField(max_length=32)
    description           = models.CharField(max_length=255)
    expiry_date           = models.DateTimeField()
    sent_at               = models.DateTimeField(blank=True, null=True)
    num_of_resends        = models.PositiveSmallIntegerField(default=0)
    created_on            = models.DateTimeField(auto_now_add=True)
    last_updated          = models.DateTimeField(auto_now=True)
    is_used               = models.BooleanField(default=False, blank=True, null=True)
    used_at               = models.DateTimeField(blank=True, null=True)
    deletion_scheduled_at = models.DateTimeField(blank=True, null=True)
   
 
    def __str__(self):
        return f"Verification for {self.user}"
        
    @classmethod
    def get_by_user(cls, user: User) -> User | None:
        """"""
        return cls.objects.filter(user=user)
    
    @classmethod
    def get_by_user_and_code(cls, user: User, verification_code: str) -> User | None:
        """"""
        try:
           return cls.objects.get(user=user, verification_code=verification_code)
        except cls.DoesNotExist:
            return None
    
    def set_expiry(self, minutes: int = 10, hours: int = 0, days: int = 0) -> None:
        if not all(isinstance(value, int) for value in (minutes, hours, days)):
              raise ValueError(
                _(
                    "Expiry values must be integers. "
                    f"Got: minutes={type(minutes).__name__}, "
                    f"hours={type(hours).__name__}, "
                    f"days={type(days).__name__}"
                )
            )
        
        if (minutes < 0 or hours < 0 or days < 0):
             raise ValueError(
                _(
                    "The value cannot be less than 0. Values can be 0 or greater "
                    f"Got: minutes={minutes}, "
                    f"hours={hours}, "
                    f"days={days}"
                )
            )

        self.expiry_date = timezone.now() + timedelta(minutes=minutes, hours=hours, days=days)
             
    def is_code_expired(self) -> bool:
        """"""
        return timezone.now() >= self.expiry_date
    
    def get_expiry_seconds(self) -> int:
        if not self.expiry_date:
            return 0
        delta = self.expiry_date - timezone.now()
        return int(delta.total_seconds())
    
    def can_resend(self) -> bool:
        """"""
        if self.is_code_expired():
            return False
        
        if self.num_of_resends >= settings.MAX_VERIFICATION_CODE_RESENDS_PER_USER:
            return False

        cooldown_passed = timezone.now() >= (
            self.sent_at + timedelta(seconds=settings.RESEND_COOLDOWN_PERIOD_IN_SECONDS)
        )
        return cooldown_passed
    
    def increment_resend(self, commit: bool = True) -> Verification | None:

        if not self.can_resend():
            raise ValidationError(_("Cannot resend yet."))

        self.num_of_resends += 1
        self.sent_at = timezone.now()

        if commit:
             self.save(update_fields=["num_of_resends", "sent_at"])
             return self
    
    def mark_as_used(self, commit = True):

        now          = timezone.now()
        self.is_used = True
        self.used_at = now

        self.deletion_scheduled_at = now + timedelta(seconds=self.get_expiry_seconds())

        if commit:
            self.save()
            return self
    
    def mark_as_expired(self, commit = True):
        """"""
        self.deletion_scheduled_at = timezone.now() + timedelta(seconds=self.get_expiry_seconds())

        if commit:
            self.save()
            return self
        
    def save(self, *args, **kwargs):
        if not self.expiry_date:
            raise ValidationError(_("expiry_date must be set before saving."))
        
        if not self.pk:
            self.sent_at = timezone.now()

        return super().save(*args, **kwargs)
    

class EmailLog(EmailBaseLog):
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"To email: {self.to_email} from {self.from_email}"
  

