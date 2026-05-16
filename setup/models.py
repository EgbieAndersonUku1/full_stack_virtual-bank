from __future__ import annotations


from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password, identify_hasher
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


User = get_user_model()


# Create your models here.

class Pin(models.Model):

    pin           = models.CharField(max_length=128)
    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name="pin")
    created_on    = models.DateTimeField(auto_now_add=True)
    last_updated  = models.DateTimeField(auto_now=True)
    is_active     = models.BooleanField(default=True)
    


    @property
    def username(self):
        """Returns the username associated with the pin"""
        return self.user.username

    @classmethod
    def get_pin_by_user(cls, user: User) -> Pin | None:
        """
        Retrieve a Pin instance for a given user.

        Args:
            user (User): The user whose PIN is being retrieved.

        Returns:
            Pin | None: The Pin object if it exists, otherwise None.

        Notes:
            Returns None instead of raising Pin.DoesNotExist to simplify
            safe lookups in service layers or views.
        """
        return cls.objects.filter(user=user)
       
    
    def is_hashed(self, value: str) -> bool:
        """
        Hash and set the user's PIN securely.

        This method ensures the PIN is never stored in plain text by
        applying Django's password hashing system.

        Args:
            pin (str): The raw PIN to be hashed and stored.

        Returns:
            None
        """

        try:
            identify_hasher(value)
            return True
        except Exception:
            return False

    def set_pin(self, pin: str) -> None:
        """
        Hash and set the user's PIN securely.

        This method ensures the PIN is never stored in plain text by
        applying Django's password hashing system.

        Args:
            pin (str): The raw PIN to be hashed and stored.

        Returns:
            None
        """
        self.pin = make_password(pin)
    
    def verify_pin(self, pin: str) -> bool:
        """
        Verify a raw PIN against the stored hashed PIN.

        Args:
            pin (str): The raw PIN provided for authentication.

        Returns:
            bool: True if the PIN matches the stored hash, False otherwise.
        """
        return check_password(self.pin, pin)
    
    def save(self, *args, **kwargs):
        """
        Save the Pin instance with a safety check to ensure
        the PIN is stored in hashed form only.

        Raises:
            ValidationError: If the PIN appears to be stored in plain text.

        Notes:
            This acts as a safeguard to enforce use of set_pin()
            before saving the model.
        """
   
        if self.pin and not self.is_hashed(self.pin):
            raise ValidationError(_("The pin must not be stored in plain text. Set pin using set_pin method"))
        
        super(self, *args, **kwargs)


