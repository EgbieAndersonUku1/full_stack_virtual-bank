from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User
from utils.security.password import PasswordStrengthChecker


class RegisterForm(forms.ModelForm):

    class Meta:
        model  = User 
        fields = ["username", "email"]

    wallet_registeration_code = forms.CharField(
        label=_("Wallet registration code"),
        max_length=34,
        min_length=34,
        required=False,
        widget=forms.TextInput(attrs={
            "aria-describedby": "wallet-code-help",
            "spellcheck": False,
            "id": "wallet-code",
        })
    )
    
    password = forms.CharField(
        label=_("Password*"),
        min_length=8,
        max_length=80,
        widget=forms.PasswordInput(attrs={
            "aria-describedby": "password-rules",
            "aria-required": True,
            "id": "password",
        })
    )
    
    confirm_password = forms.CharField(
        label=_("Confirm Password*"),
        min_length=8,
        max_length=80,
        widget=forms.PasswordInput(attrs={
            "aria-describedby": "password-rules",
            "aria-required": True,
            "id": "confirm-password",
        })
    )
    
    terms_and_condition = forms.CharField(
        label=_("I agree to the terms and conditions"),
        widget=forms.CheckboxInput(attrs={
            "aria-required": True,
            "id": "terms-of-condition-checkbox",
        })
    )

    def clean_password(self):
        password = self.cleaned_data.get("password")

        if password:
            checker = PasswordStrengthChecker(password)
            if not checker.is_strong_password():
                raise forms.ValidationError(
                    _("Password must include uppercase, lowercase, number, and special character.")
                )

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        errors = {}

        if password and confirm_password and password != confirm_password:
            errors["confirm_password"] = _("Passwords do not match.")

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data