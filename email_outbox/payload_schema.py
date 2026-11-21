"""
Approved transactional email payload templates.

Payload schema version 1.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlsplit

from django.conf import settings

from utils.custom_errors import (
    EmailOutBoxPayloadIsNotADictionary,
    InvalidEmailOutBoxPayload,
    UnsupportedSecurityEvent,
    InvalidSchemaVersion
)


class EmailTypesSchemaName(StrEnum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    NOTIFICATION = "notification"


class TemplateContextFieldSchemaName(StrEnum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"
    SECURITY_ALERT = "security_alert"


PAYLOAD_SCHEMA_VERSION = 1

ALLOWED_EMAIL_TEMPLATES = {

    EmailTypesSchemaName.EMAIL_VERIFICATION: frozenset(
        {
            "verify_email",
        }
    ),
    EmailTypesSchemaName.PASSWORD_RESET: frozenset(
        {
            "reset_password",
        }
    ),
    EmailTypesSchemaName.NOTIFICATION: frozenset(
        {
            "security_alert",
        }
    ),
}

REQUIRED_TEMPLATE_CONTEXT_FIELDS = {
    TemplateContextFieldSchemaName.VERIFY_EMAIL: frozenset(
        {
            "verification_url",
        }
    ),
    TemplateContextFieldSchemaName.RESET_PASSWORD: frozenset(
        {
            "reset_url",
        }
    ),
    TemplateContextFieldSchemaName.SECURITY_ALERT: frozenset(
        {
            "event",
        }
    ),
}

ALLOWED_SECURITY_ALERT_EVENTS = frozenset(
    {
        "password_changed",
    }
)


class PayloadValidator:

    @classmethod
    def _validate_email_type(cls, email_type: str):
        if email_type not in ALLOWED_EMAIL_TEMPLATES:
            raise ValueError("Unsupported email type.")

    @classmethod
    def _validate_payload(cls, payload: dict) -> None:
        if not isinstance(payload, dict):
            raise EmailOutBoxPayloadIsNotADictionary(
                "Email payload must be a dictionary."
            )

        required_keys = frozenset(
            {
                "schema_version",
                "template",
                "context",
            }
        )

        if payload.keys() != required_keys:
            raise InvalidEmailOutBoxPayload(
                "Email payload must contain exactly "
                "schema_version, template, and context."
            )

    @classmethod
    def _validate_payload_scheme_version(cls, payload: dict):
        if (
            type(payload["schema_version"]) is not int
            or payload["schema_version"] != PAYLOAD_SCHEMA_VERSION
        ):

            raise InvalidSchemaVersion("Unsupported email payload schema version.")

    @classmethod
    def _validate_payload_template(cls, payload: dict, email_type: str) -> None:

        template = payload["template"]

        if (
            not isinstance(template, str)
            or template not in ALLOWED_EMAIL_TEMPLATES[email_type]
        ):
            raise InvalidEmailOutBoxPayload("Unsupported template for this email type.")

    @classmethod
    def _validate_payload_context(cls, payload: dict) -> None:

        context = payload["context"]
        template = payload["template"]

        if not isinstance(context, dict):
            raise InvalidEmailOutBoxPayload(
                "Email payload must contain exactly schema_version, template, and context."
            )

        required_context_fields = REQUIRED_TEMPLATE_CONTEXT_FIELDS[template]

        if context.keys() != required_context_fields:
            raise ValueError(
                "Email payload context contains missing " "or unexpected fields."
            )

    @staticmethod
    def _validate_action_url(url: Any) -> None:
        
        if not isinstance(url, str) or not url:
            raise ValueError("Email action URL must be a non-empty string.")

        try:
            parsed_url = urlsplit(url)
        except ValueError as exc:
            raise ValueError("Email action URL must be a valid HTTPS URL.") from exc

        is_valid_https = (
            parsed_url.scheme == "https"
            and bool(parsed_url.hostname)
            and parsed_url.username is None
            and parsed_url.password is None
            and not any(char.isspace() for char in url)
        )

        if not is_valid_https:
            raise ValueError("Email action URL must be a valid HTTPS URL.")

        allowed_hosts = {
            host.lower() for host in settings.EMAIL_OUTBOX_ALLOWED_URL_HOSTS
        }
        if parsed_url.hostname not in allowed_hosts:
            raise ValueError("Email action URL host is not trusted.")

    @classmethod
    def _validate_template_context(cls, payload: dict) -> None:

        template = payload["template"]
        context = payload["context"]

        if template == "security_alert":

            event = context.get("event")
            if not isinstance(event, str) or event not in ALLOWED_SECURITY_ALERT_EVENTS:
                raise UnsupportedSecurityEvent("Unsupported security alert event.")
            return

        if template in {"verify_email", "reset_password"}:
            url_field = (
                "verification_url" if template == "verify_email" else "reset_url"
            )
            cls._validate_action_url(context.get(url_field))

    @classmethod
    def validate_payload(cls, email_type: str, payload: dict) -> None:
        """
        Validate a transactional email payload.

        Raise ValueError if the payload is invalid.
        """

        cls._validate_email_type(email_type)
        cls._validate_payload(payload)
        cls._validate_payload_context(payload)
        cls._validate_payload_scheme_version(payload)
        cls._validate_payload_template(payload, email_type)
        cls._validate_template_context(payload)
