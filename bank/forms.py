from django import forms
from django.utils.translation import gettext_lazy as _

from bank.models import Bank



class AddBankForm(forms.ModelForm):
    class Meta:
        model = Bank
        fields = ["name", "country", "description", "logo", "branch_name", "address_line_1",
                  "address_line_2", "post_code", "country", "interest_period", "phone_number",
                  "minimum_opening_deposit", "offer_overdraft", "offer_saving_account",
                  "monthly_deposit",
                  ]

