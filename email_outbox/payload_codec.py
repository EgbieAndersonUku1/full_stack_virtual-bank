import json
import logging

from cryptography.fernet import InvalidToken, MultiFernet
from django.conf import settings

from email_outbox.payload_schema import PayloadValidator
from utils.custom_errors import (
    InvalidEmailOutboxFernetKey,
    InvalidEmailOutBoxPayload,
    MissingEmailOutboxFernetKey,
)
from utils.security.encryption import Encryption

logger = logging.getLogger(__name__)


def _get_fernet() -> MultiFernet:
    """
    Build and return a MultiFernet instance configured with the primary
    and fallback email outbox encryption keys.

    Reads `EMAIL_OUTBOX_FERNET_KEY` and `EMAIL_OUTBOX_OLD_FERNET_KEYS`
    from Django settings and validates their format.

    Returns:
        MultiFernet: A MultiFernet instance ready for encryption,
        decryption, and key rotation.

    Raises:
        MissingEmailOutboxFernetKey: If `EMAIL_OUTBOX_FERNET_KEY` is missing
            or empty in Django settings.
        InvalidEmailOutboxFernetKey: If the primary key or any configured
            old key is malformed or not a valid 32-byte URL-safe base64 string.
    """

    primary_key = getattr(settings, "EMAIL_OUTBOX_FERNET_KEY", None)

    if not primary_key:
        logger.info("EMAIL_OUTBOX_FERNET_KEY is not configured.")
        raise MissingEmailOutboxFernetKey("EMAIL_OUTBOX_FERNET_KEY is not configured.")

    old_keys = getattr(settings, "EMAIL_OUTBOX_OLD_FERNET_KEYS", [])

    try:
        return Encryption.build_multi_fernet(primary_key, old_keys)
    except (ValueError, TypeError, AssertionError) as exc:
        logger.critical("The email outbox key is invalid")
        raise InvalidEmailOutboxFernetKey(
            "EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with."
        ) from exc



def is_encrypted_with_primary_key(encrypted_payload: str) -> bool:
    """
    Determine whether an encrypted payload can be authenticated
    and decrypted using the current primary Fernet key.

    Return True if the primary key can decrypt the payload,
    otherwise return False.
    """
    primary_key = getattr(settings, "EMAIL_OUTBOX_FERNET_KEY", None)

    if not primary_key:
        raise MissingEmailOutboxFernetKey("EMAIL_OUTBOX_FERNET_KEY is not configured.")

    try:
        Encryption(encryption_key=primary_key).decrypt(encrypted_payload)
    except InvalidToken:
        return False
    except (ValueError, TypeError) as exc:
        raise InvalidEmailOutboxFernetKey(
            "Fernet key must be 32 url-safe base64-encoded bytes"
        ) from exc

    return True


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
        raise InvalidEmailOutBoxPayload(
            f"The encrypted payload is not a string. Got type {type(encrypted_payload).__name__}"
        )

    try:

        decrypted_bytes = _get_fernet().decrypt(encrypted_payload.encode())
        decrypted_payload = json.loads(decrypted_bytes.decode())

    except (json.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError) as exc:
        raise InvalidEmailOutBoxPayload("The payload is invalid") from exc
    except InvalidToken as exc:
        raise InvalidToken(
            "The encrypted payload could not be decrypted with the configured keys."
        ) from exc
    if not isinstance(decrypted_payload, dict):
        raise InvalidEmailOutBoxPayload(
            "The payload return is not a dictionary. "
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
        raise InvalidEmailOutBoxPayload("The encrypted payload must be a string.")

    try:
        rotated_token = _get_fernet().rotate(encrypted_payload.encode())
    except UnicodeEncodeError as exc:
        raise InvalidEmailOutBoxPayload("The encrypted payload is invalid.") from exc
    except InvalidToken as exc:
        raise InvalidToken(
            "The encrypted payload could not be decrypted with the configured keys."
        ) from exc

    return rotated_token.decode()
