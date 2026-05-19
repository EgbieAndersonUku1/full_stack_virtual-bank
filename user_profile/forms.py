from django import forms
from django.utils.translation import gettext_lazy as _


from .models import UserProfile



class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = [
                "first_name",
                "last_name",
                "middle_name",
                "gender",
                "bio",
                "phone_number",
                "profile_pic",
                "city",
                "address_line_1",
                "address_line_2",
                "postcode",
                "country",
                ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["profile_pic"].widget.attrs.update({
            "aria-describedby": "profile-pic-help",
            "id": "profile-pic",
        })

        self.fields["first_name"].widget.attrs.update({
            "id": "first-name",
            "maxlength": "20",
            "autocomplete": "given-name",
            "required": True,
            "placeholder": "e,g John.."
        })

        self.fields["last_name"].widget.attrs.update({
            "id": "last-name",
            "maxlength": "20",
            "autocomplete": "family-name",
            "required": True,
            "placeholder": "e,g Smith.."
        })

        self.fields["middle_name"].widget.attrs.update({
            "id": "middle-name",
            "maxlength": "20",
            "autocomplete": "additional-name",
             "placeholder": "e,g. Optional if you have one"
        })

        self.fields["gender"].widget.attrs.update({
            "id": "gender",
            "aria-describedby": "gender-help",
            "required": True,
        })

        self.fields["bio"].widget.attrs.update({
            "id": "bio",
            "rows": 5,
            "maxlength": "150",
            "aria-describedby": "bio-help",
             "placeholder": "Example, In my spare time I like doing...."
        })

        self.fields["phone_number"].widget.attrs.update({
            "id": "phone-number",
            "autocomplete": "tel",
            "required": True,
            "placeholder": "e,g. +44 7700 900000 (test number)"
            
        })

        self.fields["address_line_1"].widget.attrs.update({
            "id": "address-line-1",
            "maxlength": "200",
            "autocomplete": "address-line1",
            "required": True,
            "placeholder": "e,g 161A Baker Street..."
        })

        self.fields["address_line_2"].widget.attrs.update({
            "id": "address-line-2",
            "maxlength": "200",
            "autocomplete": "address-line2",
        })

        self.fields["city"].widget.attrs.update({
            "id": "city",
            "maxlength": "40",
            "autocomplete": "address-level2",
            "required": True,
            "placeholder": "e.g London.."
        })

        self.fields["postcode"].widget.attrs.update({
            "id": "postcode",
            "maxlength": "10",
            "autocomplete": "postal-code",
            "required": True,
            "placeholder": "e.g N1 AAA",
        })

        self.fields["country"].widget.attrs.update({
            "id": "country",
            "required": True,
        })


    def clean_phone_number(self):

        cleaned_phone = self.cleaned_data.get("phone_number")

        if not cleaned_phone:
            raise forms.ValidationError(_("Expected a phone number got None"))
        
        if not cleaned_phone.is_digit():
             raise forms.ValidationError(_("The phone number must contain only digits"))

        return cleaned_phone        

