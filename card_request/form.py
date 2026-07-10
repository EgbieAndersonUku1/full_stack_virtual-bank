from django import forms
from .models import CardRequestBasicInformation, CardRequestEmploymentInformation


class CardRequestForm(forms.ModelForm):
    class Meta:
        model  = CardRequestBasicInformation
        fields = ["first_name", "last_name", "phone_number", "address1", "address2", "country",
                  "city", "state", "postal_code", "card_type","card", "card_brand", "special_requests",
                 ]
        widgets = {
            "special_requests": forms.Textarea(attrs={
                "placeholder": "Enter any special instructions here..."
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        def set_placeholder(field, text):
            self.fields[field].widget.attrs.update({
                "placeholder": text,
                "class": "required-input"
            })

    
        # Text inputs
        set_placeholder("first_name", "First name...")
        set_placeholder("last_name", "Last name...")
        set_placeholder("phone_number", "+44 020 7946 0958")
        set_placeholder("address1", "Address 1")
        set_placeholder("address2", "Address 2")
        set_placeholder("state", "London")
        set_placeholder("postal_code", "N1 4AA")

        # Select IDs (UI hooks only)
        self.fields["card_type"].widget.attrs.update({
            "id": "requested-card-account-type",
            "class": "required-input"
        })

        self.fields["card"].widget.attrs.update({
            "id": "requested-card-category",
            "class": "required-input"
        })

        self.fields["card_brand"].widget.attrs.update({
            "id": "requested-card-brand",
            "class": "required-input"
        })



class CardRequestEmploymentForm(forms.ModelForm):

    employment_status_CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
    ]

    employment_status = forms.ChoiceField(
        choices=employment_status_CHOICES,
        widget=forms.RadioSelect,
        label="Are you currently employed?",
        required=True,
        initial="no",
    )

    class Meta:
        model = CardRequestEmploymentInformation
        fields = [
            "employment_type",
            "years_of_employment",
            "employer_name",
            "annual_income_range",
            "pay_frequency",
            "contract_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        employment_status = self.data.get("employment_status")

        # JS handles UI behaviour (show/hide + required toggling),
        # but frontend validation is not secure because it can be bypassed
        # (e.g. JS disabled or request sent manually).
        #
        # On the backend, Django still treats these fields as required
        # by default, so we dynamically adjust "required" here based on
        # whether the user is employed.
        #
        # If user selects "no", employment fields are not required.
        #
        if employment_status == "no":
            
            for field in [
                "employment_type",
                "years_of_employment",
                "employer_name",
                "annual_income_range",
                "pay_frequency",
                "contract_type",
                ]:
                self.fields[field].required = False


        try:
            self.fields["employer_name"].widget.attrs.update({
                "placeholder": "Enter employer name...",
                "class": "required-input",
            })
        except KeyError:
            pass

     
        def add_placeholder(field_name, placeholder_text):
            choices = list(self.fields[field_name].choices)

            # Replaces Django's default empty label
            choices[0] = ("", placeholder_text)
            
            self.fields[field_name].choices = choices
            self.fields[field_name].widget.attrs["class"] = "required-input"

     
        add_placeholder("employment_type", "Please select employment type")
        add_placeholder("years_of_employment", "Please select the number of years employed")
        add_placeholder("annual_income_range", "Please select annual salary")
        add_placeholder("pay_frequency", "Please select pay frequency")
        add_placeholder("contract_type", "Please select contract type")
        
    def clean(self):
        
        cleaned_data = super().clean()

        employment_status = cleaned_data.get("employment_status")

        # Backend validation is the source of truth.
        # Even though JS hides/controls fields on the frontend,
        # users can bypass it, so we enforce conditional validation here.
        #
        # If employed = "yes", employment fields become required.
        if employment_status == "yes":
            
            required_fields = [
                "employment_type",
                "years_of_employment",
                "employer_name",
                "annual_income_range",
                "pay_frequency",
                "contract_type",
            ]

            for field in required_fields:
                value = cleaned_data.get(field)

                if not value:
                    self.add_error(field, "This field is required.")

        return cleaned_data
   
   


class CardAgreementForm(forms.Form):
  agreed = forms.BooleanField(label="I have read and agree to the Card Request Agreement.")