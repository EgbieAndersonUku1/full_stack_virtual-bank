import json

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.test import TestCase, override_settings

from email_outbox.payload_codec import (
    _get_fernet,
    decrypt_payload,
    encrypt_payload,
    is_encrypted_with_primary_key,
    rotate_payload,
)
from email_outbox.payload_schema import EmailTypesSchemaName
from utils.custom_errors import (
    EmailOutBoxPayloadIsNotADictionary,
    InvalidEmailOutboxFernetKey,
    InvalidEmailOutBoxPayload,
    MissingEmailOutboxFernetKey,
)
from utils.security.encryption import Encryption


class EmailOutboxPayloadCodecTests(TestCase):

    @override_settings(EMAIL_OUTBOX_FERNET_KEY="Not a fernet key")
    def test_invalid_fernet_key_raise_error(self):
        """A valid configured key should create a Fernet instance."""

        with self.assertRaisesMessage(
            InvalidEmailOutboxFernetKey,
            "EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with",
        ):
            _get_fernet()

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=Encryption.generate_key())
    def test_valid_key_creates_fernet_instance(self):
        """
        A valid configured key should create a Fernet instance.
        """
        fernet_encrypt = _get_fernet()

        self.assertIsInstance(fernet_encrypt, MultiFernet)

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=None)
    def test_missing_key_raises_error(self):
        """
        A missing encryption key must raise an explicit error.
        """

        with self.assertRaisesMessage(
            MissingEmailOutboxFernetKey, "EMAIL_OUTBOX_FERNET_KEY is not configured"
        ):
            _get_fernet()

    @override_settings(EMAIL_OUTBOX_FERNET_KEY="this-is-not-a-valid-fernet-key")
    def test_invalid_key_raises_error(self):
        """
        An invalid encryption key must raise an explicit error.
        """
        with self.assertRaisesMessage(
            InvalidEmailOutboxFernetKey,
            "EMAIL_OUTBOX_FERNET_KEY is invalid or has been tampered with.",
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
        self.assertNotEqual(
            payload,
            encrypted_payload,
            "The payload and encrypted payload should not be equal",
        )

    @override_settings(EMAIL_OUTBOX_FERNET_KEY=Encryption.generate_key())
    def test_encrypt_payload_rejects_non_dictionary(self):
        """
        Email payloads must be dictionaries.
        """

        with self.assertRaisesMessage(
            EmailOutBoxPayloadIsNotADictionary,
            "Email payload must be a dictionary.",
        ):
            encrypt_payload(
                EmailTypesSchemaName.NOTIFICATION, "this is not a dictionary"
            )

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

        with self.assertRaisesMessage(
            MissingEmailOutboxFernetKey, "EMAIL_OUTBOX_FERNET_KEY is not configured."
        ):
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
        self.assertEqual(
            decrypted_payload, payload, "Decrypted and original payload should match"
        )

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

        with self.assertRaisesMessage(
            InvalidToken,
            "The encrypted payload could not be decrypted with the configured keys.",
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

        encryption = Encryption(encryption_key)
        encrypted_payload = encryption.encrypt(payload)

        # override the key in the settings by replacing it with another key
        with override_settings(EMAIL_OUTBOX_FERNET_KEY=decryption_key):

            with self.assertRaisesMessage(
                InvalidToken,
                "The encrypted payload could not be decrypted with the configured keys.",
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

    @override_settings()
    def test_decrypt_payload_with_old_key(self):
        old_key = Encryption.generate_key()
        new_key = Encryption.generate_key()

        payload = {"message": "Test key rotation"}
        encryption = Encryption(old_key)

        encrypted_payload = encryption.encrypt(payload)

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=new_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key],
        ):
            decrypted_payload = decrypt_payload(encrypted_payload)

        self.assertEqual(decrypted_payload, payload)

    def test_encrypt_payload_uses_primary_key(self):
        primary_key = Encryption.generate_key()
        old_key = Encryption.generate_key()

        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": "password_changed",
            },
        }

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key],
        ):

            encrypted_payload_with_primary_key = encrypt_payload(
                EmailTypesSchemaName.NOTIFICATION, payload
            )

            decrypted_payload = Encryption(primary_key).decrypt(
                encrypted_payload_with_primary_key, to_json=True
            )

            self.assertEqual(payload, decrypted_payload)

        with self.assertRaises(InvalidToken):
            Encryption(old_key).decrypt(
                encrypted_payload_with_primary_key, to_json=True
            )

    def test_decrypt_payload_rejects_removed_old_key(self):
        old_key = Encryption.generate_key()
        new_key = Encryption.generate_key()

        payload = {"message": "Encrypted with removed key"}

        # Encrypt using the old key
        encrypted_payload = Encryption(old_key).encrypt(payload)

        # remove the old key and test if decryption fails
        with override_settings(EMAIL_OUTBOX_OLD_FERNET_KEYS=[new_key]):

            with self.assertRaisesMessage(
                InvalidToken,
                "The encrypted payload could not be decrypted with the configured keys.",
            ):
                decrypt_payload(encrypted_payload)

            # test if the next key is picked up instead of the old key when _get_fernet() is called
            encrypted_payload_with_new_key = (
                _get_fernet().encrypt(json.dumps(payload).encode()).decode()
            )
            decrypt_payload(encrypted_payload_with_new_key)

    def test_invalid_old_fernet_key_raises_error(self):
        primary_key = Encryption.generate_key()

        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": "password_changed",
            },
        }

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=["invalid-old-key"],
        ):
            with self.assertRaises(InvalidEmailOutboxFernetKey):
                encrypt_payload(
                    EmailTypesSchemaName.NOTIFICATION,
                    payload,
                )

    def test_rotate_old_token_to_primary_key(self):

        old_key = Encryption.generate_key()
        primary_key = Encryption.generate_key()

        payload = {"message": "Test token rotation"}

        old_token = Encryption(old_key).encrypt(payload)

        multi_fernet = MultiFernet(
            [
                Fernet(primary_key),
                Fernet(old_key),
            ]
        )

        rotated_token = multi_fernet.rotate(
            old_token
        )  # decrypts with the old key and then immediately re-encrypts with the new key

        decrypted_payload = Encryption(primary_key).decrypt(rotated_token, to_json=True)

        self.assertEqual(decrypted_payload, payload)

        with self.assertRaises(InvalidToken):
            Encryption(old_key).decrypt(rotated_token)

    def test_rotate_payload_uses_primary_key(self):

        old_key = Encryption.generate_key()
        primary_key = Encryption.generate_key()

        payload = {"message": "Application-level rotation"}

        old_token = Encryption(old_key).encrypt(payload)

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[primary_key, old_key],
        ):

            rotated_token = rotate_payload(old_token)

            decrypted_payload = Encryption(primary_key).decrypt(
                rotated_token, to_json=True
            )

            self.assertEqual(decrypted_payload, payload)

        with self.assertRaises(InvalidToken):
            Encryption(old_key).decrypt(rotated_token)

    def test_is_encrypted_with_primary_key_returns_true(self):

        old_key = Encryption.generate_key()
        primary_key = Encryption.generate_key()
        payload = {"message": "Application-level rotation"}

        encrypted_payload = Encryption(primary_key).encrypt(payload)
        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[primary_key, old_key],
        ):

            is_decrypted = is_encrypted_with_primary_key(encrypted_payload)
        self.assertTrue(is_decrypted)

    def test_is_encrypted_with_primary_key_returns_false_for_old_key(self):
        primary_key = Encryption.generate_key()
        old_key = Encryption.generate_key()

        encrypted_payload = Encryption(old_key).encrypt("Test payload")

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key],
        ):

            result = is_encrypted_with_primary_key(encrypted_payload)

        self.assertFalse(result)

    def test_is_encrypted_with_primary_key_returns_false_for_unknown_key(self):

        primary_key = Encryption.generate_key()
        unknown_key = Encryption.generate_key()

        encrypted_payload = Encryption(unknown_key).encrypt("Test payload")

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[],
        ):

            result = is_encrypted_with_primary_key(encrypted_payload)

        self.assertFalse(result)

    def test_is_encrypted_with_primary_key_returns_false_for_corrupted_token(self):
        primary_key = Encryption.generate_key()

        corrupted_payload = "this-is-not-a-valid-fernet-token"

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[],
        ):
            result = is_encrypted_with_primary_key(corrupted_payload)

        self.assertFalse(result)


