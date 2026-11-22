import json
import logging

from cryptography.fernet import InvalidToken
from django.conf import settings

from email_outbox.payload_schema import PayloadValidator
from cryptography.fernet import MultiFernet
from utils.custom_errors import (
    InvalidEmailOutboxFernetKey,
    InvalidEmailOutBoxPayload,
    MissingEmailOutboxFernetKey,
    )

from utils.security.encryption import Encryption

logger = logging.getLogger(__name__)


def _get_fernet() -> MultiFernet:

    try:
        key = settings.EMAIL_OUTBOX_FERNET_KEY
    except AttributeError as e:
        error_msg = str(e)
        logger.info(error_msg)
        raise AttributeError(error_msg)

    if key is None:
        raise MissingEmailOutboxFernetKey("EMAIL_OUTBOX_FERNET_KEY is not configured.")

    try:
        return Encryption.build_multi_fernet(key,settings.EMAIL_OUTBOX_OLD_FERNET_KEYS)
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

    serialized_payload = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return _get_fernet().encrypt(serialized_payload).decode()


def decrypt_payload(encrypted_payload: str) -> dict:
    """
    Decrypt an email payload and return its original dictionary.
    """

    if not isinstance(encrypted_payload, str):
        raise InvalidEmailOutBoxPayload(f"The encrypted payload is not a string. Got type {type(encrypted_payload).__name__}"
                                        )

    try:

        decrypted_bytes   = _get_fernet().decrypt(encrypted_payload.encode())
        decrypted_payload = json.loads(decrypted_bytes.decode())

    except (json.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError) as exc:
        raise InvalidEmailOutBoxPayload("The payload is invalid") from exc
    except InvalidToken as exc:
        raise InvalidToken(
            "The encrypted payload could not be decrypted with the configured keys."
        ) from exc
    if not isinstance(decrypted_payload, dict):
        raise InvalidEmailOutBoxPayload("The payload return is not a dictionary. "
                                        f"Got type {type(decrypted_payload).__name__}"
                                        )
    return decrypted_payload



def rotate_payload(encrypted_payload: str) -> str:
    """
    Re-encrypt an existing email payload using the current
    primary Fernet key.

    Previous keys must remain configured to decrypt older tokens.
    """
    if not isinstance(encrypted_payload, str):
        raise InvalidEmailOutBoxPayload(
            "The encrypted payload must be a string."
        )

    try:
        rotated_token = _get_fernet().rotate(
            encrypted_payload.encode()
        )
    except UnicodeEncodeError as exc:
        raise InvalidEmailOutBoxPayload(
            "The encrypted payload is invalid."
        ) from exc
    except InvalidToken as exc:
        raise InvalidToken(
            "The encrypted payload could not be decrypted with the configured keys."
        ) from exc

    return rotated_token.decode()
