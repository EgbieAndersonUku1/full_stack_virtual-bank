from django.test import TestCase, override_settings
from cryptography.fernet import InvalidToken

from email_outbox.payload_codec import (
    _get_fernet,
    encrypt_payload,
    decrypt_payload
)

from email_outbox.payload_schema import EmailTypesSchemaName
from utils.custom_errors import (
    EmailOutBoxPayloadIsNotADictionary,
    InvalidEmailOutBoxPayload,
    InvalidEmailOutboxFernetKey,
    MissingEmailOutboxFernetKey
)

from utils.security.encryption import Encryption


class EmailOutboxPayloadCodecTests(TestCase):

    @override_settings(EMAIL_OUTBOX_FERNET_KEY="Not a fernet key")
    def test_invalid_fernet_key_raise_error(self):
        """A valid configured key should create a Fernet instance.
        """

        with self.assertRaisesMessage(InvalidEmailOutboxFernetKey,
                                      "EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with",
                                      ):
             _get_fernet()

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=Encryption.generate_key())
    def test_valid_key_creates_fernet_instance(self):
        """
        A valid configured key should create a Fernet instance.
        """
        fernet_encrypt = _get_fernet()

        self.assertIsInstance(fernet_encrypt, Encryption)

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=None)
    def test_missing_key_raises_error(self):
        """
        A missing encryption key must raise an explicit error.
        """

        with self.assertRaisesMessage(MissingEmailOutboxFernetKey,
            "EMAIL_OUTBOX_FERNET_KEY is not configured"
            ):
            _get_fernet()

    @override_settings(EMAIL_OUTBOX_FERNET_KEY="this-is-not-a-valid-fernet-key")
    def test_invalid_key_raises_error(self):
        """
        An invalid encryption key must raise an explicit error.
        """
        with self.assertRaisesMessage(InvalidEmailOutboxFernetKey,
            "EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with."
            ):

            _get_fernet()

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=Encryption.generate_key())
    def test_encrypt_payload_returns_valid_fernet_token(self):
        """
        Encrypting a dictionary should produce a valid Fernet token.
        """
        payload = {
             "schema_version": 1,
             "template": "security_alert",
             "context": {
                    "event": "password_changed",
                    },
                }

        encrypted_payload = encrypt_payload(EmailTypesSchemaName.NOTIFICATION, payload)
        self.assertIsInstance(encrypted_payload, str)
        self.assertNotEqual(payload,
                            encrypted_payload,
                            "The payload and encrypted payload should not be equal"
                            )

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=Encryption.generate_key())
    def test_encrypt_payload_rejects_non_dictionary(self):
        """
        Email payloads must be dictionaries.
        """

        with self.assertRaisesMessage(EmailOutBoxPayloadIsNotADictionary,
                                      "Email payload must be a dictionary.",
                                      ):
            encrypt_payload(EmailTypesSchemaName.NOTIFICATION, "this is not a dictionary")

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=None)
    def test_encrypt_payload_rejects_missing_key(self):
        """
        Encryption must fail when the Fernet key is missing.
        """
        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": "password_changed",
                        },
        }

        with self.assertRaisesMessage(MissingEmailOutboxFernetKey, "EMAIL_OUTBOX_FERNET_KEY is not configured."):
            encrypt_payload(EmailTypesSchemaName.NOTIFICATION, payload)

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=Encryption.generate_key())
    def test_encrypt_decrypt_round_trip(self):
        """
        Encrypting and decrypting a payload must preserve its data.
        """

        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": "password_changed",
            },
        }

        encrypted_payload = encrypt_payload(EmailTypesSchemaName.NOTIFICATION, payload)
        decrypted_payload = decrypt_payload(encrypted_payload)

        # test if it matches the original
        self.assertEqual(decrypted_payload, payload, "Decrypted and original payload should match")

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=Encryption.generate_key())
    def test_decrypt_payload_rejects_tampered_token(self):
        """
        Decryption must reject an encrypted token that has been modified.
        """

        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": "password_changed",
            },
        }

        encrypted = encrypt_payload(EmailTypesSchemaName.NOTIFICATION, payload)
        replacement = "A" if encrypted[-2] != "A" else "B"
        tampered = encrypted[:-2] + replacement + encrypted[-1]

        with self.assertRaisesMessage(InvalidToken,
                                      "EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with."
                                      ):
            decrypt_payload(tampered)

    def test_decrypt_payload_rejects_non_string_input(self):
        """
        Decryption must reject inputs that are not strings.
        """
        with self.assertRaisesMessage(
            InvalidEmailOutBoxPayload,
            "The encrypted payload is not a string. Got type dic",
        ):
            decrypt_payload({"encrypted": "not-a-token"})

    def test_decrypt_payload_rejects_wrong_key(self):
        """
        A token encrypted with a different Fernet key must be rejected.
        """

        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {"event": "password_changed"},
        }

        # call a fresh encryption to encrypt because encrypt_payload usisng the setting key
        encryption_key = Encryption.generate_key()
        decryption_key = Encryption.generate_key()

        encryption        = Encryption(encryption_key)
        encrypted_payload = encryption.encrypt(payload)

        # override the key in the settings by replacing it with another key
        with override_settings(EMAIL_OUTBOX_FERNET_KEY=decryption_key):

            with self.assertRaisesMessage(InvalidToken,
                                     "EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with.",
                                     ):
                decrypt_payload(encrypted_payload)

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=Encryption.generate_key())
    def test_encrypt_payload_rejects_invalid_security_alert_event(self):
        """
        Encryption must reject an invalid security-alert event before
        attempting encryption.
        """
        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": {"one", "two"},
            },
        }

        with self.assertRaisesMessage(
            ValueError,
            "Unsupported security alert event.",
        ):
            encrypt_payload(EmailTypesSchemaName.NOTIFICATION, payload)

