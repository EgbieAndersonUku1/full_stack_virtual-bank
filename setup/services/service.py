from __future__ import annotations

import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _



from bank.services import AccountService
from bank.models import Bank, BankAccount
from card.services import BankCardService
from setup.models import Pin

from user_profile.models import UserProfile
from utils.utils import validate_params_are_strings
from utils.send_email import send_welcome_email_with_async
from utils.custom_errors import OnBoardingFailureError


User = get_user_model()
logger = logging.Logger(__name__)


class AccountOnboardingService:

    @classmethod
    def _create_profile(cls, user: User, profile_data: dict) -> UserProfile:

        if not isinstance(user, User):
           raise TypeError(
                    _("The user is not a user instance. Got type %(type)s with value %(value)s")
                    % {
                        "type": type(user).__name__,
                        "value": user,
                    }
                )


        validate_params_are_strings(profile_data)

        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "email": user.email,
            },
        )

        for field, value in profile_data.items():
            setattr(user_profile, field, value)

        user_profile.email = user.email
        user_profile.save()

        return user_profile


    @classmethod
    def _create_pin(cls, pin: str, user: User, user_profile: UserProfile) -> bool:

        if pin == None:
            raise OnBoardingFailureError(_("The pin was not created during onboarding steps"))

        if not isinstance(pin, str):
            logger.debug("Pincreation failed during onboarding process")
            raise OnBoardingFailureError(_("Pin creation failed during onboarding"))

        if not isinstance(user, User):
            raise TypeError(_("Expected a user instance. Got object with type %s") %(type(user).__name__))

        pin_obj, _ = Pin.objects.get_or_create(user=user, user_profile=user_profile)
        pin_obj.set_pin(pin=pin)
        pin_obj.save()
        return True

    @classmethod
    def _send_welcome_email(cls, bank_account: BankAccount,
                             user_profile: UserProfile,
                             subject: str = "Welcome email"
                             ):

        send_welcome_email_with_async(subject = subject,
                                      email=user_profile.email,
                                      first_name=user_profile.first_name,
                                      last_name=user_profile.last_name,
                                      account_last_4=bank_account.account_last_four_digits,
                                      sort_code_masked=bank_account.sortcode_last_four_digits,
                                      bank_name=bank_account.bank_name,
                                       )
    @classmethod
    def complete_onboarding(cls,
                            user: User,
                            bank: Bank,
                            profile_data: dict,
                            pin: str) -> bool:


        user_profile, bank_account = None, None

        with transaction.atomic():

            user_profile = cls._create_profile(user=user, profile_data=profile_data)
            bank_account = AccountService.open_bank_account(bank=bank, user_profile=user_profile)

            if bank.offer_saving_account == Bank.OfferSavingAccountOptions.YES:
                 AccountService.open_bank_account(bank=bank, user_profile=user_profile, account_type=BankAccount.AccountType.SAVINGS)

            cls._create_pin(pin=pin, user=user, user_profile=user_profile)

            BankCardService.create_default_bank_card(bank_account)

        if not bank_account:
            logger.debug("Bank account creation failed during onboarding process")
            raise OnBoardingFailureError(_("Bank account creation failed during onboarding"))

        if not user_profile:
            logger.debug("User profile creation failed during onboarding process")
            raise OnBoardingFailureError(_("User profile creation failed during onboarding"))


        cls._send_welcome_email(bank_account=bank_account,
                                user_profile=user_profile
                                )
        return True
