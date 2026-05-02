from __future__ import annotations
from enum import Enum
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
        


class VerificationStatus(Enum):
    USED     = "used"
    LOCKED   = "locked"
    COOLDOWN = "cooldown"
    RESENT   = "resent"

    
class Verification(models.Model):

    class VerificationType(models.TextChoices):
        EMAIL_VERIFICATION        = "EV", _("Email Verification")
        PASSWORD_VERIFICATION     = "PV", _("Password Verification")
        PASSWORD_RESET            = "PR", _("Password Reset")
    
    class Status(models.TextChoices):
        PENDING  = "P", _("Pending")
        VERIFIED = "S", _("Verified")
        EXPIRED  = "E", _("Expired")
        BLOCKED  = "B", _("Blocked")
     
    user                   = models.ForeignKey(User, on_delete=models.CASCADE)
    verification_code      = models.CharField(max_length=32)
    description            = models.CharField(max_length=255)
    expiry_date            = models.DateTimeField()
    sent_at                = models.DateTimeField(blank=True, null=True)
    num_of_resend_requests = models.PositiveSmallIntegerField(default=0)
    created_on             = models.DateTimeField(auto_now_add=True)
    last_updated           = models.DateTimeField(auto_now=True)
    is_used                = models.BooleanField(default=False, blank=True, null=True)
    used_at                = models.DateTimeField(blank=True, null=True)
    verification_type      = models.CharField(max_length=2, choices=VerificationType, 
                                             default=VerificationType.EMAIL_VERIFICATION)
    status                = models.CharField(max_length=1, choices=Status, default=Status.PENDING)
    deletion_scheduled_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "verification_type"],
                name="unique_user_verification_type"
            )
        ]

    def __str__(self):
        return f"Verification for {self.user}"
        
    @classmethod
    def get_by_user_and_type(cls, user: User, verification_type: str) -> User | None:
        """"""
        return cls.objects.filter(user=user, verification_type=verification_type).first()
    
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

    @property  
    def is_code_expired(self) -> bool:
        """"""
        return timezone.now() >= self.expiry_date
    
    def get_expiry_seconds(self) -> int:
        if not self.expiry_date:
            return 0
        delta = self.expiry_date - timezone.now()
        return int(delta.total_seconds())
    
    def is_resend_limit_exceeded(self):
        """"""
        return self.num_of_resend_requests >= settings.MAX_VERIFICATION_CODE_RESENDS_PER_USER
    
    @property
    def cooldown_ends_at(self):
        return self.sent_at + timedelta(
            seconds=settings.RESEND_COOLDOWN_PERIOD_IN_SECONDS
        )

    @property
    def cooldown_seconds_left(self):
        remaining = self.cooldown_ends_at - timezone.now()
        return max(0, int(remaining.total_seconds()))


    def can_resend(self) -> bool:
        """"""
        if self.is_used:
            return False

        if self.is_resend_limit_exceeded():
            return False

        if timezone.now() < self.cooldown_ends_at:
            return False

        return True
        
    def increment_resend(self, commit: bool = True) -> Verification | None:

        if not self.can_resend():
            raise ValidationError(_("Cannot resend yet."))

        self.num_of_resend_requests += 1
        self.sent_at = timezone.now()
        fields_to_update = ["num_of_resend_requests", "sent_at"]

        if self.is_resend_limit_exceeded():
            fields_to_update.append("status")
            self.mark_as_blocked(commit=False)

        if commit:
             self.save(update_fields=fields_to_update)
             return self
    
    def mark_as_used(self, commit: bool = True) -> Verification | None:

        now              = timezone.now()
        self.is_used     = True
        self.used_at     = now
        self.status      = self.Status.VERIFIED
        self.description = "Verification code successfully used and verified"
 
        self.deletion_scheduled_at = now + timedelta(seconds=self.get_expiry_seconds())

        if commit:
            self.save()
            return self
    
    def mark_as_expired(self, commit = True) -> Verification | None:
        """"""
        self.deletion_scheduled_at = timezone.now() + timedelta(seconds=self.get_expiry_seconds())
        self.status = self.Status.EXPIRED
        self.description = "Verification code has expired"

        if commit:
            self.save()
            return self
    
    def mark_as_blocked(self, commit = True) -> Verification | None:
        """"""
        self.status      = self.Status.BLOCKED
        self.description = "Verification has been blocked and can't be used any longer"

        if commit:
            self.save()
            return self
        
    @property
    def is_blocked(self) -> bool:
        return self.status == self.Status.BLOCKED
    
    def get_status(self) -> str:
        if self.is_used:
            return VerificationStatus.USED

        if self.is_resend_limit_exceeded():
            return VerificationStatus.LOCKED

        if not self.can_resend():
            return VerificationStatus.COOLDOWN

        return VerificationStatus.RESENT
    
    def save(self, *args, **kwargs):
        if not self.expiry_date:
            self.set_expiry(minutes=settings.DEFAULT_CODE_EXPIRY_IN_MINUTES)
        
        if not self.pk:
            self.sent_at = timezone.now()

        return super().save(*args, **kwargs)
    


class VerificationPending(Verification):
    """
    Proxy model for admin use.

    Provides a filtered view of Verification objects
    with status = PENDING in the admin page, making it 
    easier to manage pending verifications without manual filtering.
    """
    class Meta:
        proxy               = True
        verbose_name        = "Pending Verification"
        verbose_name_plural = "Pending Verifications"


class VerificationBlock(Verification):
    """
    Proxy model for admin use.

    Provides a filtered view of Verification objects
    with status = BLOCKED in the admin page, making it 
    easier to manage blocked verifications without manual filtering.
    """
    class Meta:
        proxy = True
        verbose_name = "Blocked Verification"
        verbose_name_plural = "Blocked Verifications"


class VerificationUsed(Verification):
    """
    Proxy model for admin use.

    Provides a filtered view of Verification objects
    with status = USED in the admin page, making it 
    easier to manage used verifications without manual filtering.
    """
    class Meta:
        proxy = True
        verbose_name = "Used Verification"
        verbose_name_plural = "Used Verifications"


class VerificationExpired(Verification):
    """
    Proxy model for admin use.

    Provides a filtered view of Verification objects
    with status = EXPIRED in the admin page, making it 
    easier to manage expired verifications without manual filtering.
    """
    class Meta:
        proxy = True
        verbose_name = "Expired Verification"
        verbose_name_plural = "Expired Verifications"




class EmailLog(EmailBaseLog):
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"To email: {self.to_email} from {self.from_email}"
  




