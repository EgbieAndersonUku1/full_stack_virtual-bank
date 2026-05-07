from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField


# Create your models here.

class UserProfile(models.Model):
    
    first_name    = models.CharField(max_length=20)
    last_name     = models.CharField(max_length=20)
    middle_name   = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField()
    country       = CountryField(blank_label="(select country)")
    city          = models.CharField(max_length=40)
    postcode      = models.CharField(max_length=10)

    def __str__(self):
        return _(f"{self.first_name} {self.last_name} is from {self.country}")
    