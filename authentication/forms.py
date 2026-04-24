
from django import forms
from .models import User


class RegisterForm(forms.ModelForm):

    class Meta:
        model  = User 
        fields = ["username", "email"]

    # username = forms.CharField(label="Username*", 
    #                            max_length=80,
    #                            min_length=3, 
    #                            widget=forms.TextInput(
    #                                attrs={
    #                                  "aria-required": True,
    #                                }
    #                            ))
    
    # email    = forms.EmailField(label="Email*", max_length=200, 
    #                             widget=forms.EmailInput(
    #                                 attrs={
    #                                     "aria-required": True,
    #                                 }
    #                             ))
    
    wallet_registeration_code = forms.CharField(label="Wallet registeration code", 
                                                max_length=34,
                                                min_length=34,
                                                required=False,
                                                widget=forms.TextInput(attrs={
                                                    "aria-describedby": "wallet-code-help",
                                                    "spellcheck": False,
                                                    "id": "wallet-code",
                                                    "required": False,
                                                  
                                                })
                                                )
    
    password = forms.CharField(label="Password*", 
                               
                               min_length=8,
                               max_length=80,
                               widget=forms.PasswordInput(
                                attrs={
                                     "aria-describedby" : "password-rules" ,
                                      "aria-required": True,
                                      "id": "password",

                                }
                         ))
    
    confirm_password = forms.CharField(label="Confirm Password*", 
                               min_length=8,
                               max_length=80,
                               widget=forms.PasswordInput(
                                attrs={
                                     "aria-describedby" : "password-rules" ,
                                      "aria-required": True,
                                      "id": "confirm-password"
                                }
                         ))
    
    terms_and_condition = forms.CharField(widget=forms.CheckboxInput(attrs={
        "aria-required": True,
        "id": "terms-of-condition-checkbox",
    }))