
from __future__ import annotations

from django.db import models
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from django_ckeditor_5.fields import CKEditor5Field
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxLengthValidator
from django.contrib.auth import get_user_model

from user_profile.models import UserProfile


User = get_user_model()


# Create your models here.

class CardRequestApplication(models.Model):
    
    class Status(models.TextChoices):
        PENDING  = "Pending", _("Pending")
        ACCEPTED = "Accepted", _("Accepted")
        REJECTED =  "Rejected", _("Rejected")
        WITHDRAWN = "withdrawn", _("Withdrawn")
        CANCELLED = "cancelled", _("Cancelled")
        
    user             = models.ForeignKey(User, on_delete=models.CASCADE)
    status           = models.CharField(choices=Status.choices, max_length=15, default=Status.PENDING)
    created_on       = models.DateTimeField(auto_now_add=True)
    last_modified_on = models.DateTimeField(auto_now_add=True)
    reviewed_on      = models.DateTimeField(blank=True, null=True)
    notes            = models.TextField(validators=[MaxLengthValidator(2000)], blank=True, null=True)
    reviewed_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_card_applications")
    submitted_on     = models.DateTimeField(blank=True, null=True)
    
    def can_submit_application(self):
        return not self.has_pending_application()
    
    @classmethod
    def has_pending_application(cls, user: User) -> bool:
        cls._check_if_user_instance(user)
        return cls.objects.filter(user=user, status=cls.Status.PENDING).exists()
        
    @classmethod
    def number_of_applications(cls, user: User) -> int:
        cls._check_if_user_instance(user)
        return cls.objects.filter(user=user).count()
    
    @classmethod
    def get_user_applications(cls, user: User, status=None):
        """
        Retrieve card request applications submitted by a specific user.

        Optionally filters the results by application status (for example,
        pending, accepted, or rejected). Related objects are eagerly loaded
        to minimise additional database queries when accessing the associated
        user, basic information, or employment information.

        Args:
            user (User):
                The user whose card request applications should be retrieved.

            status (str, optional):
                An application status from ``CardRequestApplication.Status``.
                If omitted, all applications for the user are returned.

        Raises:
            TypeError:
                If ``user`` is not an instance of ``User``.

        Returns:
            QuerySet[CardRequestApplication]:
                A queryset containing the user's card request applications.
        """

        cls._check_if_user_instance(user)
        queryset = (
            cls.objects
            .select_related("user", "basic_information", "employment_information")
            .filter(user=user)
        )

        if status is not None:
            queryset = queryset.filter(status=status)

        return queryset
    
    @classmethod
    def _check_if_user_instance(cls, user: User) -> None:
        if not isinstance(user, User):
            raise TypeError(
                f"Expected a User instance, got {type(user).__name__}."
            )
    
    @property
    def applicant_full_name(self):
        return self.user.profile.full_name
    
    def __str__(self):
        return str(self.user)
    

class QueryProfile(models.Model):
    """
    Abstract base model that provides shared query helpers
    for models linked to a UserProfile.
    """

    class Meta:
        abstract = True

    @classmethod
    def get_by_user(cls, user) -> UserProfile | None:
        """
        Return the first record matching the given UserProfile.

        Args:
            user_profile (UserProfile): The user profile instance to filter by.

        Returns:
            Model instance or None: The first matching record, or None if not found.

        Raises:
            ValueError: If user_profile is not a UserProfile instance.
        """
        if not isinstance(user, User):
            raise ValueError(
                f"user must be an instance of User. "
                f"Expected User, got {type(user).__name__}"
            )

        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None
    

class CardRequestBasicInformation(QueryProfile):
    
    class CardType(models.TextChoices):
        VIRTUAL   = "virtual", _("Virtual")
        PHYSICAL  = "physical", _("Physical")
        TEMPORARY = "temporary", _("Temporary")

    class Card(models.TextChoices):
        CREDIT = "credit", _("Credit")
        DEBIT  = "debit", _("Debit")

    class CardBrand(models.TextChoices):
        VISA       = "visa", _("Visa")
        MASTERCARD = "mastercard", _("Mastercard")
        DISCOVER   = "discover", _("Discover")

    application = models.ForeignKey(CardRequestApplication, 
                                               on_delete=models.CASCADE, 
                                               related_name="basic_information", 
                                               null=True,
                                               blank=True)
    first_name             = models.CharField(max_length=100, verbose_name="First name*")
    last_name              = models.CharField(max_length=100, verbose_name="Last name*")
    email                  = models.EmailField(max_length=100, verbose_name="Email*")
    phone_number           = PhoneNumberField(max_length=20, verbose_name="Phone number*")
    address1               = models.CharField(max_length=255, verbose_name="Addess line 1*")
    address2               = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address line 2")
    country                = CountryField(blank_label="(select country)", null=True, verbose_name="Bank Country*")
    city                   = models.CharField(max_length=100, verbose_name="City*")
    state                  = models.CharField(max_length=100, verbose_name="State*")
    postal_code            = models.CharField(max_length=20, verbose_name="Post code*")
    special_requests       = models.TextField(blank=True, null=True, max_length=500, verbose_name="Special instructions")
    card_type              = models.CharField(max_length=20, choices=CardType.choices, default=CardType.VIRTUAL, verbose_name="Card type*")
    card                   = models.CharField(max_length=20, choices=Card.choices, default=Card.DEBIT, verbose_name="Card*")
    card_brand             = models.CharField(max_length=20, choices=CardBrand.choices, default=CardBrand.VISA, verbose_name="Card brand*")
    created_on             = models.DateTimeField(auto_now_add=True)
    last_modified_on       = models.DateTimeField(auto_now=True)
    
  
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return ""

    @classmethod
    def get_by_user_profile(cls, user_profile):
        if not isinstance(user_profile, UserProfile):
            raise ValueError("user_profile must be an instance of UserProfile. Expected UserProfile, got {}".format(type(user_profile).__name__)    )
        return cls.objects.filter(user_profile=user_profile).first()
    
    @property
    def get_full_address(self):
        address_parts = [self.address1, self.address2, self.city, self.state, self.postal_code, self.country.name]
        return ', '.join(filter(None, address_parts))
    
    def __str__(self):
        return self.full_name
    
    

class CardRequestEmploymentInformation(QueryProfile):
    
    class EmploymentStatus(models.TextChoices):
        EMPLOYED = "employed", _("Employed")
        UNEMPLOYED = "unemployed", _("Unemployed")

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", _("Full-time")
        PART_TIME = "part_time", _("Part-time")
        CONTRACT  = "contract", _("Contract")
        TEMPORARY = "temporary", _("Temporary")
        INTERN    = "intern", _("Intern")
        SELF_EMPLOYED = "self_employed", _("Self-employed")

    class YearsOfEmployment(models.TextChoices):
        LESS_THAN_ONE = "less_than_one", _("Less than 1 year")
        ONE_TO_THREE  = "one_to_three", _("1-3 years")
        THREE_TO_FIVE = "three_to_five", _("3-5 years")
        FIVE_TO_TEN   = "five_to_ten", _("5-10 years")
        MORE_THAN_TEN = "more_than_ten", _("More than 10 years")

    class AnnualIncomeRange(models.TextChoices):
        LESS_THAN_15K = "less_than_15k", _("Less than 15,000")
        FROM_15K_TO_24K = "from_15k_to_24k", _("15,000 - 24,000")
        FROM_24K_TO_34K = "from_24k_to_34k", _("24,000 - 34,000")
        FROM_34K_TO_44K = "from_34k_to_44k", _("34,000 - 44,000")
        FROM_44K_TO_54K = "from_44k_to_54k", _("44,000 - 54,000")
        FROM_54K_TO_64K = "from_54k_to_64k", _("54,000 - 64,000")
        FROM_64K_TO_74K = "from_64k_to_74k", _("64,000 - 74,000")
        FROM_74K_TO_84K = "from_74k_to_84k", _("74,000 - 84,000")
        FROM_84K_TO_94K = "from_84k_to_94k", _("84,000 - 94,000")
        FROM_94K_TO_104K = "from_94k_to_104k", _("94,000 - 104,000")
        HIGHER_THAN_104K = "higher_than_104k", _("Higher than 104,000")

    class PayFrequency(models.TextChoices):
        WEEKLY = "weekly", _("Weekly")
        BI_WEEKLY = "bi_weekly", _("Bi-weekly")
        SEMI_MONTHLY = "semi_monthly", _("Semi-monthly")
        MONTHLY = "monthly", _("Monthly")
        ANNUALLY = "annually", _("Annually")

    class ContractType(models.TextChoices):
        PERMANENT = "permanent", _("Permanent")
        TEMPORARY = "temporary", _("Temporary")
        CONTRACT  = "contract", _("Contract")
        FREELANCE = "freelance", _("Freelance")
        INTERN    = "intern", _("Intern")
        AGENCY_WORKER = "agency_worker", _("Agency Worker")
            
    application         = models.OneToOneField(CardRequestApplication, on_delete=models.CASCADE, related_name="employment_information")
    employer_name       = models.CharField(max_length=20, verbose_name="Employer name *", blank=True, null=True)
    employment_status   = models.CharField(max_length=20, choices=EmploymentStatus.choices, verbose_name="Employer status*")
    employment_type     = models.CharField(max_length=20, choices=EmploymentType.choices)
    years_of_employment = models.CharField(max_length=20, choices=YearsOfEmployment.choices)
    annual_income_range = models.CharField(max_length=20, choices=AnnualIncomeRange.choices)
    pay_frequency       = models.CharField(max_length=20, choices=PayFrequency.choices)
    contract_type       = models.CharField(max_length=20, choices=ContractType.choices)
    created_on          = models.DateTimeField(auto_now_add=True)
    last_modified_on    = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return f"Employment Information for {self.application.applicant_full_name}"
    
    


class CardRequestAgreement(models.Model):
    
    title              = models.CharField(max_length=80, blank=True, null=True)
    terms_of_condition = CKEditor5Field("Terms of conditions", config_name="default")
    created_on         = models.DateTimeField(auto_now_add=True)
    last_modified_on   = models.DateTimeField(auto_now=True)
   

class CardRequestApplicationLog(models.Model):
    
    class Action(models.TextChoices):
        APPLICATION_SUBMITTED = "application_submitted", _("Application Submitted")
        STATUS_CHANGED        = "status_changed", _("Status Changed")
        REVIEW_COMPLETED      = "review_completed", _("Review Completed")
        NOTES_ADDED           = "notes_added", _("Notes Added")
    
    action           = models.CharField(choices=Action.choices, max_length=25)
    user             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username         = models.CharField(max_length=60)
    email            = models.EmailField(max_length=100)
    full_name        = models.CharField(max_length=100)
    notes            = models.TextField(blank=True)
    created_on       = models.DateTimeField(auto_now_add=True)
    last_modified_on = models.DateTimeField(auto_now=True)
    
    
    @classmethod
    def get_all_user_logs(cls, user: User, action = None) -> QuerySet[CardRequestApplicationLog] :
        cls._validate_user_instance(user)
        
        if action == None:
            return cls.objects.filter(user=user)
        
        if not isinstance(action, str):
            raise TypeError(f"Expected a string for action. Got type {type(action).__name__}")
    
        return cls.objects.filter(user=user, action=action)
    
    @classmethod
    def _validate_user_instance(cls, user: User):
        if not isinstance(user, User):
            raise TypeError(f"Expected a user instance. Got object with type {type(user).__name__}")
        