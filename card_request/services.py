from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.db import DatabaseError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.safe_cache import set_cache_with_retry
from .models import (CardRequestApplication, 
                     CardRequestApplicationLog, 
                     CardRequestBasicInformation, 
                     CardRequestEmploymentInformation
                     )


logger = logging.getLogger("application")
User   = get_user_model()


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
    def add_card_request_to_database(cls, basic_information: dict, 
                                     employment_information: dict, user: User) -> CardRequestApplication:
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
       
        cls._validate(basic_information, employment_information,  user)
               
        try:
            with transaction.atomic():
                  
                application = CardRequestApplication.objects.create(user=user, submitted_on=timezone.now())
            
                # add basic information
                basic_information_obj = CardRequestBasicInformation(**basic_information)
                basic_information_obj.application = application
                basic_information_obj.email = user.email
                basic_information_obj.save()
                
                # add employment information
                employment_information_obj = CardRequestEmploymentInformation(**employment_information)
                employment_information_obj.application = application
                employment_information_obj.save()
            
                logger.info("Storing basic information and employment information for user {}".format(user))  
                
            
                # create audit log entry
                CardRequestApplicationLog.objects.create(
                    action=CardRequestApplicationLog.Action.APPLICATION_SUBMITTED,
                    user=user,
                    username=user.username,
                    email=user.email,
                    full_name=user.profile.full_name
                )
            
                # only save the cache if transaction.atomic is saved
                transaction.on_commit(
                        lambda: cls._cache_application_state(
                            user.username,
                            application.status
                        )
                    )
                
        except DatabaseError:
            logger.exception("Failed to create card request application for user %s", user.username)
            raise

        logger.info("Successfully created card request application %s for user %s", application.id, user.username)

        return application
    
    @classmethod
    def _cache_application_state(cls, username: str, application_status: str) -> None:
        
        cache_key = construct_card_application_session_key(username)
        set_cache_with_retry(key=cache_key, value=application_status, ttl=None)
        
    
    @classmethod
    def _validate(cls, basic_information: dict, employment_information: dict, user: User) -> None:
        if not isinstance(basic_information, dict):
            error_msg = "Expected basic_information to be a dict. Got type {}"
            raise TypeError(cls._build_error_message(error_msg, basic_information))
        
        if not isinstance(employment_information, dict):
            error_msg = "Expected employment_information to be a dict. Got type {}"
            raise TypeError(cls._build_error_message(error_msg, employment_information))
        
        
        if not isinstance(user, User) :
            error_msg = "Expected user to be a User instance. Got type {}"
            raise TypeError(cls._build_error_message(error_msg, user))
        
    @classmethod
    def _build_error_message(cls, msg: str, error_value: Any) -> str:
        return _(msg.format(type(error_value).__name__))
        
    