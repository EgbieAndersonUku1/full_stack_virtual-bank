from django import forms


class PinConfirmCodeForm(forms.Form):
    pin = forms.CharField(
        max_length=6,
        min_length=6,
        required=False,
        widget=forms.HiddenInput(attrs={
            "id": "pin-confirmation",
        })  
    )

    def clean_code(self):
        pin = self.cleaned_data.get("pin")
        MAXIMUM_ALLOWED_LENGTH = 6
      
        if not pin.isdigit():
            raise forms.ValidationError(_("Pin must contain only digits."))
        
        pin_length = len(pin)
        if pin_length < MAXIMUM_ALLOWED_LENGTH:
            raise forms.ValidationError(_(f"The maximum length of the code must be {MAXIMUM_ALLOWED_LENGTH}. Got code with length {pin_length} "))

        return pin