from django.test import SimpleTestCase

from email_outbox.payload_schema import (
    EmailTypesSchemaName,
    PayloadValidator,
    TemplateContextFieldSchemaName,
    )

from utils.custom_errors import InvalidEmailOutBoxPayload, InvalidSchemaVersion


class EmailOutboxPayloadSchemaTests(SimpleTestCase):

    def test_valid_security_alert_payload(self):
        """
        A valid security alert payload should pass validation.
        """
        payload = {
            "schema_version": 1,
            "template": TemplateContextFieldSchemaName.SECURITY_ALERT,
            "context": {
                "event": "password_changed",
            },
        }

        self.assertIsNone(PayloadValidator.validate_payload("notification", payload))

    def test_rejects_unsupported_email_type(self):
        """
        Unsupported email types must be rejected.
        """

        payload = {
            "schema_version": 1,
            "template": TemplateContextFieldSchemaName.SECURITY_ALERT,
            "context": {
                "event": "password_changed",
            },
        }

        with self.assertRaisesMessage(ValueError, "Unsupported email type."):
            PayloadValidator.validate_payload("Marketing", payload)

    def test_rejects_missing_top_level_field(self):
        """
        Payloads missing required top-level fields
        must be rejected.
        """
        payload = {
            "schema_version": 1,
            "template": TemplateContextFieldSchemaName.SECURITY_ALERT,
        }

        with self.assertRaisesMessage(
            InvalidEmailOutBoxPayload,
            "Email payload must contain exactly schema_version, template, and context.",
        ):
            PayloadValidator.validate_payload(EmailTypesSchemaName.NOTIFICATION, payload)


    def test_rejects_unexpected_top_level_field(self):
        """
        Payloads containing unexpected top-level fields must be rejected.
        """
        payload = {
            "schema_version": 1,
            "template": TemplateContextFieldSchemaName.SECURITY_ALERT,
            "context": {
                "event": "password_changed",
            },
            "password": "should-not-be-here",
        }

        with self.assertRaisesMessage(
            ValueError,
            "Email payload must contain exactly "
            "schema_version, template, and context.",
        ):
            PayloadValidator.validate_payload(EmailTypesSchemaName.NOTIFICATION, payload)

    def test_rejects_unsupported_schema_version(self):
        """
        Payloads using unsupported schema versions
        must be rejected.
        """
        # A string schema version should fail because the system accept integer

        invalid_schemas = ["1", 2, 2.0] # str, wrong version and a float

        payload = {
            "schema_version": "1",
            "template": TemplateContextFieldSchemaName.SECURITY_ALERT,
                "context": {
                    "event": "password_changed",
                },

                }

        for invalid_schema in invalid_schemas:
             payload["schema_version"] = invalid_schema
             with self.subTest(invalid_schemas):
                with self.assertRaisesMessage(
                    InvalidSchemaVersion,
                    "Unsupported email payload schema version."
                    ):
                    PayloadValidator.validate_payload(EmailTypesSchemaName.NOTIFICATION, payload)

    def test_rejects_template_for_wrong_email_type(self):
        """
        A template must belong to its specified email type.
        """
        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": "password_changed",
            },
        }

        with self.assertRaisesMessage(
            ValueError,
            "Unsupported template for this email type.",
        ):
            PayloadValidator.validate_payload("password_reset", payload)

    def test_rejects_unexpected_context_fields(self):
        """
        Context dictionaries must not containunexpected fields.
        """
        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": "password_changed",
                "password": "should-not-be-here",
            },
        }

        with self.assertRaisesMessage(
            ValueError,
            "Email payload context contains missing "
            "or unexpected fields.",
        ):
            PayloadValidator.validate_payload("notification", payload)

    def test_rejects_unsupported_security_alert_event(self):
        """
        Security alerts must use an approved event.
        """
        payload = {
            "schema_version": 1,
            "template": "security_alert",
            "context": {
                "event": "account_locked",
            },
        }

        with self.assertRaisesMessage(
            ValueError,
            "Unsupported security alert event.",
        ):
            PayloadValidator.validate_payload(EmailTypesSchemaName.NOTIFICATION, payload)

    def test_rejects_http_password_reset_url(self):
        """
        Password-reset URLs must use HTTPS.
        """
        payload = {
            "schema_version": 1,
            "template": "reset_password",
            "context": {
                "reset_url": (
                    "http://localhost/password/"
                    "reset_password/john/example-token/"
                ),
            },
        }

        with self.assertRaisesMessage(
            ValueError,
            "Email action URL must be a valid HTTPS URL.",
        ):
            PayloadValidator.validate_payload("password_reset", payload)

    def test_rejects_untrusted_password_reset_host(self):
        """
        Password-reset URLs must use an approved host.
        """
        payload = {
            "schema_version": 1,
            "template": "reset_password",
            "context": {
                "reset_url": (
                    "https://attacker.example/password/"
                    "reset_password/john/example-token/"
                ),
            },
        }

        with self.assertRaisesMessage(
            ValueError,
            "Email action URL host is not trusted.",
        ):
            PayloadValidator.validate_payload("password_reset", payload)

    def test_accepts_valid_password_reset_url(self):
        """
        A password-reset URL using HTTPS and a trusted
        host should pass validation.
        """
        payload = {
            "schema_version": 1,
            "template": "reset_password",
            "context": {
                "reset_url": (
                    "https://localhost/password/"
                    "reset_password/john/example-token/"
                ),
            },
        }

        self.assertIsNone(
            PayloadValidator.validate_payload(EmailTypesSchemaName.PASSWORD_RESET, payload)
        )

    def test_accepts_valid_email_verification_url(self):
        """
        A verification URL using HTTPS and a trusted
        host should pass validation.
        """
        payload = {
            "schema_version": 1,
            "template": "verify_email",
            "context": {
                "verification_url": (
                    "https://localhost/verify/example-token/"
                ),
            },
        }

        self.assertIsNone(
            PayloadValidator.validate_payload(EmailTypesSchemaName.EMAIL_VERIFICATION, payload)
        )
