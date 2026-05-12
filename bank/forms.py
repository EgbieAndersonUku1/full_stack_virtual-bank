from django import forms
from django.utils.translation import gettext_lazy as _

from bank.models import Bank



class AddBankForm(forms.ModelForm):
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  

        if "phone_number" in self.fields:
            self.fields["phone_number"].widget.attrs.update({"minlength": "10", 
                                                             "maxlength": "15", 
                                                             "placeholder": "e.g. +44 7700 900000 (test number)" })
            
            self.fields["interest_rate"].widget.attrs.update({"step": "0.01",
                                                              "min": "0",
                                                              "max": "100",
                                                             })
            
            self.fields["monthly_deposit"].widget.attrs.update({"step": "0.01",
                                                              "min": "0",
                                                              "max": "100",
                                                             })
            self.fields["minimum_opening_deposit"].widget.attrs.update({"step": "0.01",
                                                              "min": "0",
                                                              "max": "100",
                                                             })


    class Meta:
        model = Bank
        fields = ["name", "country", "description", "logo", "branch_name", "address_line_1",
                  "address_line_2", "post_code", "country", "interest_period", "phone_number",
                  "minimum_opening_deposit", "offer_overdraft", "offer_saving_account",
                  "monthly_deposit", "interest_rate",
                  ]

    def save(self, commit=True):
        
        instance = super().save(commit=False)
        interest_rate_in_percentage = self.cleaned_data["interest_rate"].get("interest_rate")
        instance.interest_rate_bps  =  int(round(interest_rate_in_percentage * 100))

        if commit:
            instance.save()

        return instance

        