from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bank.services.bank_services import BankAccountCacheService
from utils.custom_errors import CardRequestApplicationTypeError
from utils.safe_cache import get_cache_or_set, set_cache_with_retry
from utils.utils import format_boolean_as_text

from .models import (
    CardRequestApplication,
    CardRequestApplicationLog,
    CardRequestBasicInformation,
    CardRequestEmploymentInformation,
)

logger = logging.getLogger("application")

User = get_user_model()


ALL_CARD_APPLICATION_CACHE_KEY = "card_request_user_applications"


EMPLOYMENT_STATUS_FORM_MAPPING = {
    "yes": CardRequestEmploymentInformation.EmploymentStatus.EMPLOYED,
    "no": CardRequestEmploymentInformation.EmploymentStatus.UNEMPLOYED,
}


def construct_card_application_session_key(username: str) -> str:
    """
    Constructs the session cache key for a user's card application.

    The generated key uniquely identifies the user's card application
    data in the session or cache.

    Args:
        username: The user's username.

    Returns:
        The session key in the format ``"<username>__card_application"``.

    Raises:
        ValueError: If ``username`` is ``None``.
        TypeError: If ``username`` is not a string.
    """
    if username is None:
        raise ValueError("Username cannot be None.")

    if not isinstance(username, str):
        error_msg = "Expected a username string. Got value with type {}"
        raise TypeError(CardRequestService._build_error_message(error_msg, username))

    return f"{username}__card_application"


class CardRequestService:
    """
    Provides business logic for managing card request applications.

    This service handles the creation of card request applications by
    coordinating the creation of related models, including applicant
    information, employment information, audit logs, and application
    status caching.

    Database operations are performed atomically to ensure that a card
    request application is either completely saved or fully rolled back
    if an error occurs.

    This class contains workflow logic rather than presentation logic,
    allowing views and other components to interact with the card request
    process without directly managing model relationships.
    """

    @classmethod
    def add_card_request_to_database(
        cls, basic_information: dict, employment_information: dict, user: User
    ) -> CardRequestApplication:
        """
        Creates and stores a complete card request application.

        This method creates the parent CardRequestApplication record and
        associates the submitted basic information and employment information
        with it. The operation is wrapped inside a database transaction to
        ensure that either the entire application is saved successfully or
        no records are created.

        After successfully creating the application, an audit log entry is
        created to record that the application was submitted, and the user's
        cached application status is updated to reflect the current state.

        Args:
            basic_information (dict): Validated applicant information used to
                create the CardRequestBasicInformation record.

            employment_information (dict): Validated employment details used
                to create the CardRequestEmploymentInformation record.

            user (User): The authenticated user submitting the card request.

        Raises:
            TypeError: If basic_information or employment_information are not
                dictionaries, or if user is not a User instance.

            DatabaseError: If any database operation fails, causing the
                transaction to be rolled back.

        Returns:
            CardRequestApplication: The newly created card request application.
        """

        cls._validate(basic_information, employment_information, user)

        try:
            with transaction.atomic():

                application = CardRequestApplication.objects.create(
                    user=user, submitted_on=timezone.now()
                )

                # add basic information
                basic_information_obj = CardRequestBasicInformation(**basic_information)
                basic_information_obj.application = application
                basic_information_obj.email = user.email
                basic_information_obj.save()

                # add employment information
                employment_information_copy = employment_information.copy()

                employment_information_copy["employment_status"] = (
                    EMPLOYMENT_STATUS_FORM_MAPPING[
                        employment_information_copy["employment_status"].lower()
                    ]
                )

                employment_information_obj = CardRequestEmploymentInformation(
                    **employment_information_copy
                )
                employment_information_obj.application = application
                employment_information_obj.save()

                logger.info(
                    "Storing basic information and employment information for user {}".format(
                        user
                    )
                )

                # create audit log entry
                CardRequestApplicationLog.objects.create(
                    action=CardRequestApplicationLog.Action.APPLICATION_SUBMITTED,
                    user=user,
                    username=user.username,
                    email=user.email,
                    full_name=user.profile.full_name,
                )

                # only save the cache if transaction.atomic is saved
                transaction.on_commit(
                    lambda: cls._cache_application_state(
                        user.username, application.status
                    )
                )

        except DatabaseError:
            logger.exception(
                "Failed to create card request application for user %s", user.username
            )
            raise

        logger.info(
            "Successfully created card request application %s for user %s",
            application.id,
            user.username,
        )

        return application

    @classmethod
    def _cache_application_state(cls, username: str, application_status: str) -> None:

        cache_key = construct_card_application_session_key(username)
        set_cache_with_retry(key=cache_key, value=application_status, ttl=None)

        # update the overall cache
        set_cache_with_retry(
            key=ALL_CARD_APPLICATION_CACHE_KEY,
            value=CardRequestApplication.get_applications(),
        )

        logger.info("Added to information to cache")

    @classmethod
    def _validate(
        cls, basic_information: dict, employment_information: dict, user: User
    ) -> None:
        if not isinstance(basic_information, dict):
            error_msg = "Expected basic_information to be a dict. Got type {}"
            raise TypeError(cls._build_error_message(error_msg, basic_information))

        if not isinstance(employment_information, dict):
            error_msg = "Expected employment_information to be a dict. Got type {}"
            raise TypeError(cls._build_error_message(error_msg, employment_information))

        if not isinstance(user, User):
            error_msg = "Expected user to be a User instance. Got type {}"
            raise TypeError(cls._build_error_message(error_msg, user))

    @classmethod
    def _build_error_message(cls, msg: str, error_value: Any) -> str:
        return _(msg.format(type(error_value).__name__))


class CardRequestsApplicationCacheService:
    """
    Provides cached access to card request applications.

    This service retrieves card request applications from a shared cache,
    falling back to the database when the cache is unavailable. It also
    provides convenience methods for filtering applications by status and
    retrieving application statistics.

    Using this service helps reduce repeated database queries when displaying
    administrative dashboards and card request workflow information.
    """

    @classmethod
    def get_applications(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve all card request applications.

        Returns:
            QuerySet[CardRequestApplication]: A queryset containing every
            card request application.
        """
        return cls._get_from_cache()

    @classmethod
    def get_under_review_applications(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve applications currently under review.

        Returns:
            QuerySet[CardRequestApplication]: Applications whose status is
            UNDER_REVIEW.
        """
        return cls._get_from_cache().filter(
            status=CardRequestApplication.Status.UNDER_REVIEW
        )

    @classmethod
    def get_pending_applications(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve applications awaiting administrative review.

        Returns:
            QuerySet[CardRequestApplication]: Applications whose status is
            PENDING.
        """
        return cls._get_from_cache().filter(
            status=CardRequestApplication.Status.PENDING
        )

    @classmethod
    def get_on_hold_applications(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve applications that have been placed on hold.

        Returns:
            QuerySet[CardRequestApplication]: Applications whose status is
            ON_HOLD.
        """
        return cls._get_from_cache().filter(
            status=CardRequestApplication.Status.ON_HOLD
        )

    @classmethod
    def get_rejected_applications(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve rejected card request applications.

        Returns:
            QuerySet[CardRequestApplication]: Applications whose status is
            REJECTED.
        """
        return cls._get_from_cache().filter(
            status=CardRequestApplication.Status.REJECTED
        )

    @classmethod
    def get_approved_applications(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve approved card request applications.

        Returns:
            QuerySet[CardRequestApplication]: Applications whose status is
            ACCEPTED.
        """
        return cls._get_from_cache().filter(
            status=CardRequestApplication.Status.ACCEPTED
        )

    @classmethod
    def get_cancelled_applications(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve cancelled card request applications.

        Returns:
            QuerySet[CardRequestApplication]: Applications whose status is
            CANCELLED.
        """
        return cls._get_from_cache().filter(
            status=CardRequestApplication.Status.CANCELLED
        )

    @classmethod
    def get_withdrawn_applications(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve withdrawn card request applications.

        Returns:
            QuerySet[CardRequestApplication]: Applications whose status is
            WITHDRAWN.
        """
        return cls._get_from_cache().filter(
            status=CardRequestApplication.Status.WITHDRAWN
        )

    @classmethod
    def _get_from_cache(cls) -> QuerySet[CardRequestApplication]:
        """
        Retrieve all card request applications from the cache.

        If the cache is empty, the applications are loaded from the database,
        cached, and then returned.

        Raises:
            AttributeError: Raised if the cached object or queryset cannot be
                retrieved correctly.

        Returns:
            QuerySet[CardRequestApplication]: Cached queryset containing all
            card request applications.
        """
        try:
            return get_cache_or_set(
                key=ALL_CARD_APPLICATION_CACHE_KEY,
                value_or_func=lambda: CardRequestApplication.get_applications(),
            )
        except AttributeError as e:
            raise AttributeError(_(str(e)))

    @classmethod
    def update_cache(cls):
        """
        Refresh the card request application cache.

        Retrieves the latest card request applications from the database and
        repopulates the cache to ensure cached data remains consistent with the
        current database state.

        This method should be called after creating, updating, or deleting a
        card request application.
        """
        set_cache_with_retry(
            key=ALL_CARD_APPLICATION_CACHE_KEY,
            value=lambda: CardRequestApplication.get_applications(),
        )

    @classmethod
    def get_by_status(cls, status: str) -> QuerySet[CardRequestApplication]:
        """
        Retrieve card request applications matching the provided workflow status.

        This method retrieves applications through the existing cache-backed
        application retrieval layer and filters the results by the supplied
        application status.

        The status value should match one of the available
        CardRequestApplication.Status choices, such as:
        - pending
        - under_review
        - accepted
        - rejected
        - cancelled
        - withdrawn
        - on_hold

        Args:
            status (str): The workflow status used to filter applications.

        Returns:
            QuerySet[CardRequestApplication]: A queryset containing applications
            matching the requested status.

        Raises:
            TypeError: If the provided status is not a string.
        """

        if not isinstance(status, str):
            logger.info(
                _(
                    "The status value for the CardRequestApplicationCacheService.get_by_status(...) class is not a string"
                )
            )
            raise TypeError(
                _(
                    "Expected a string but got object with type {object_type}".format(
                        object_type=type(status).__name__
                    )
                )
            )

        if status.lower() not in CardRequestApplication.Status.values:

            logger.info(
                _(
                    "The status value enter doesn't match the expected value. "
                    "Expected values ['pending', 'on_holding', 'accepted', "
                    "'rejected', 'withdrawn', 'cancelled', 'under_review']"
                )
            )
            raise ValueError(
                _("Invalid card request application status: {status}").format(
                    status=status
                )
            )
        return cls.get_applications().filter(status=status)

    @classmethod
    def get_applications_status_count(cls) -> dict[str, int]:
        """
        Return application counts grouped by workflow status.

        This method is primarily intended for dashboard summary cards where
        administrators need a quick overview of application volumes across
        each stage of the review workflow.

        Returns:
            dict[str, int]: A dictionary containing the number of applications
            for each status and the total application count.
        """
        return {
            "pending": cls.get_pending_applications().count(),
            "rejected": cls.get_rejected_applications().count(),
            "cancelled": cls.get_cancelled_applications().count(),
            "withdrawn": cls.get_withdrawn_applications().count(),
            "on_hold": cls.get_on_hold_applications().count(),
            "all": cls.get_applications().count(),
            "under_review": cls.get_under_review_applications().count(),
            "approved": cls.get_approved_applications().count(),
        }

    @classmethod
    def get_by_application_id(
        cls, application_id: str
    ) -> CardRequestApplication | None:
        """
        Retrieve a cached card request application by its application ID.

        Args:
            application_id (str):
                The unique identifier assigned to a card request application.

        Returns:
            CardRequestApplication | None:
                The cached card request application if found; otherwise, None.

        Raises:
            TypeError:
                Raised if ``application_id`` is not a string.
        """
        if not isinstance(application_id, str):
            raise TypeError(
                _(
                    "Expected a string got application"
                    " id with {application_type}".format(
                        application_type=type(application_id).__name__
                    )
                )
            )

        return cls.get_applications().filter(application_id=application_id).first()

    @classmethod
    def get_number_of_applications_for_user(cls, user: User) -> int:
        return cls.get_applications().filter()


def build_application_response_data(application: CardRequestApplication) -> dict[str]:
    """
    Build the response data required by the card request review endpoint.

        Extracts and organises application, customer, account, and bank
        information into a structured dictionary that is returned as part
        of the JSON response.

        Args:
            application (CardRequestApplication):
                The card request application being reviewed.

        Returns:
            dict:
                A dictionary containing the application information required
                by the card request review interface.
    """

    if not isinstance(application, CardRequestApplication):
        raise CardRequestApplicationTypeError(
            _(
                "Expected a card request application instance. Got application with type {}"
            ).format(type(application).__name__)
        )

    basic_information = application.basic_information
    bank_accounts     = BankAccountCacheService.get_accounts(application.user)
    current_account   = bank_accounts.first()
    account_number    = current_account.account_last_four_digits
    sort_number       = current_account.sortcode_last_four_digits
    phone_number      = current_account.sort_code.bank.phone_number
    profile           = current_account.user_profile
    user              = application.user

    context = {
        "APPLICATION_ID": application.application_id,
        "STATUS": application.status,
        "SUBMISSION_DATE": application.submitted_on,
        "REQUEST_CARD_INFO": {
            "CARD": basic_information.full_card,
            "CARD_VARIANT": basic_information.card_type,
            "RECIPIENT_ADDRESS": basic_information.full_address,
            "PHONE_NUMBER": str(basic_information.phone_number),
            "SPECIAL_REQUESTS": basic_information.special_requests,
        },
        # user information given during the card request application not the same as profile information
        "USER_INFORMATION": {
            "FULL_NAME": basic_information.full_name,
            "PHONE_NUMBER": str(basic_information.phone_number),
            "ADDRESS": basic_information.full_address,
            "EMAIL_ADDRESS": basic_information.email,
            "PROFILE_PIC": user.profile.profile_img,
            "PASSPORT": "",
            "NATIONALITY": "",
            "PREFFERED_LANGUAGE": "",
        },
        "USER_STATS": {
            "TOTAL_ACCOUNTS": bank_accounts.count(),
            "TOTAL_CARDS": 0,  # keep as 0 since it hasn't been built yet
            "TOTAL_TRANSACTIONS": 0,  #  keep as 0 since it hasn't been built yet,
            "ACCOUNT_BALANCE": current_account.balance,
            "TOTAL_APPLICATIONS": application.get_user_applications(user).count(),
        },
        "ACCOUNT_DETAILS": {
            "SORT_CODE": sort_number,
            "ACCOUNT_NUMBER": account_number,
            "BALANCE": current_account.balance,
            "CAN_REQUEST_OVERDRAFT": format_boolean_as_text(
                current_account.sort_code.bank.offer_overdraft
            ),
            "HAS_SAVING_ACCOUNTS": format_boolean_as_text(
                current_account.sort_code.bank.offer_saving_account
            ),
            "CAN_REQUEST_LOAN": format_boolean_as_text(
                current_account.sort_code.bank.offer_loans
            ),
            "CURRENCY": "£",  # to be added later for now use £
            "CURRENCY_CODE": "GBP", # to be added later for now use GBP
            "TYPE": current_account.account_type,
            "STATUS": current_account.status,
            "ACCOUNT_LAST_FOUR_DIGITS": account_number.split("*")[-1],
            "SORT_CODE_LAST_FOUR_DIGITS": sort_number.split("*")[-1],
            "MEMBER_SINCE": current_account.user_profile.user.created_on,
        },
        "BANK_DETAILS": {
            "BRANCH_NAME": current_account.sort_code.bank.branch_name,
            "PHYSICAL_LOCATION": current_account.sort_code.bank.full_address,
            "ADDRESS_LINE_1": current_account.sort_code.bank.address_line_1,
            "ADDRESS_LINE_2": current_account.sort_code.bank.address_line_2,
            "POSTCODE": current_account.sort_code.bank.post_code,
            "COUNTRY": current_account.sort_code.bank.country.name,
            "FULL_PHONE_NUMBER": str(phone_number),
            "COUNTRY_PHONE_NUMBER_CODE": phone_number.country_code,
            "EXT": phone_number.extension,
            "NATIONAL_NUMBER": phone_number.national_number,
            "LOGO": current_account.sort_code.bank.get_static_logo,
            "NAME": current_account.sort_code.bank.name.title(),
            "STATUS": "Active" if current_account.sort_code.bank else "Deactivated",

        },

        "CARD_HISTORY" : {
            "ACTIVE_CARDS": 0,
            "REPLACEMENT_CARDS": 0,
            "LOST_CARDS": 0,
            "STOLEN_CARDS": 0
        },

        "PROFILE_INFORATION" : {
            "FULL_NAME": profile.full_name,
            "PHONE_NUMBER": {
                "EXT": phone_number.extension,
                "NATIONAL_NUMBER": phone_number.national_number,
                "COUNTRY_CODE": phone_number.country_code,
            },
            "ADDRESS": profile.full_address,
            "EMAIL_ADDRESS": {
                "EMAIL": profile.email,
                "IS_VERIFIED": user.is_user_email_verified()
            },

            # not yet built
            "PASSPORT": {
                "IS_VERIFIED": False,
                "PASSPORT": "N/A"
            },
            "NATIONALITY": "N/A",
            "PREF_LANGUAGE": "English", # for now use English since the preferred languages hasn't been implmented yet
        }
    }
    return context
