import logging

from json import JSONDecodeError
from cryptography.fernet import InvalidToken
from django.conf import settings

from email_outbox.payload_schema import PayloadValidator
from utils.custom_errors import (
    InvalidEmailOutboxFernetKey,
    InvalidEmailOutBoxPayload,
    MissingEmailOutboxFernetKey,
    EmailOutBoxPayloadIsNotADictionary
    )

from utils.security.encryption import Encryption

logger = logging.getLogger(__name__)


def _get_fernet() -> Encryption:

    try:
        key = settings.EMAIL_OUTBOX_FERNET_KEY
    except AttributeError as e:
        error_msg = str(e)
        logger.info(error_msg)
        raise AttributeError(error_msg)

    if key is None:
        raise MissingEmailOutboxFernetKey("EMAIL_OUTBOX_FERNET_KEY is not configured.")

    try:
        return Encryption(key)
    except (ValueError, TypeError, AssertionError) as exc:
        logger.critical("The email outbox key is invalid")
        raise InvalidEmailOutboxFernetKey(
            "EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with."
        ) from exc


def encrypt_payload(email_type: str, payload: dict) -> str:
    """
    Encrypt an email payload dictionary using Fernet with
    the settings.EMAIL_OUTBOX_FERNET_KEY.

    Returns an encrypted token suitable for database storage.
    """
    # _get_fernet() returns an Encryption instance, which allows both strings
    # and dictionaries. Since this payload must strictly be a dictionary,
    # we validate the type explicitly before encrypting
    PayloadValidator.validate_payload(email_type, payload)
   
    return  _get_fernet().encrypt(payload)


def decrypt_payload(encrypted_payload: str) -> dict:
    """
    Decrypt an email payload and return its original dictionary.
    """

    if not isinstance(encrypted_payload, str):
        raise InvalidEmailOutBoxPayload(f"The encrypted payload is not a string. Got type {type(encrypted_payload).__name__}"
                                        )

    try:
        decrypted_payload = _get_fernet().decrypt(encrypted_payload, to_json=True)
    except (JSONDecodeError, UnicodeDecodeError):
        raise InvalidEmailOutBoxPayload("The payload is invalid")
    except InvalidToken:
        raise InvalidToken("EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with.")

    if not isinstance(decrypted_payload, dict):
        raise InvalidEmailOutBoxPayload("The payload return is not a dictionary. "
                                        f"Got type {type(decrypted_payload).__name__}"
                                        )
    return decrypted_payload
