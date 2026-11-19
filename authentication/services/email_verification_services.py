import logging
from dataclasses import dataclass
from enum import StrEnum
from django.conf import settings
from django.db import transaction
from human_seconds.converter import SecondsToTime

from authentication.models import (
    User,
    Verification,
    VerificationStatus,
)

from utils.security.generator import generate_secure_code
from utils.send_email import send_confirmation_email_with_async

logger = logging.getLogger(__name__)


class EmailVerificationOutcome(StrEnum):
    NOT_FOUND = "not_found"
    ALREADY_USED = "already_used"
    LOCKED = "locked"
    COOLDOWN = "cooldown"
    CODE_SCHEDULED = "code_scheduled"
    ERROR = "error"



@dataclass
class EmailVerificationResult:
    outcome: EmailVerificationOutcome
    cooldown_seconds: int | None = None
    expiry_time: str | None = None


class EmailVerificationService:

    @classmethod
    def request_new_code(cls, user: User)-> EmailVerificationResult:

        with transaction.atomic():

            verification = Verification.get_by_user_and_type(
                user=user,
                verification_type=Verification.VerificationType.EMAIL_VERIFICATION,
                for_update=True,
            )

            if verification is None:
                return EmailVerificationResult(
                    outcome=EmailVerificationOutcome.NOT_FOUND
                )

            status = verification.get_status()

            if status is None:
                logger.error(
                    "Verification.get_status() returned None unexpectedly. "
                    "User ID: %s, Verification ID: %s",
                    user.pk,
                    verification.pk,
                )

                return EmailVerificationResult(
                    outcome=EmailVerificationOutcome.ERROR
                )

            match status:

                case VerificationStatus.USED:
                    return EmailVerificationResult(
                        outcome=EmailVerificationOutcome.ALREADY_USED
                    )

                case VerificationStatus.LOCKED:
                    return EmailVerificationResult(
                        outcome=EmailVerificationOutcome.LOCKED
                    )

                case VerificationStatus.COOLDOWN:
                    return EmailVerificationResult(
                        outcome=EmailVerificationOutcome.COOLDOWN,
                        cooldown_seconds=verification.cooldown_seconds_left,
                    )

                case VerificationStatus.CAN_SEND:
                    secure_code = generate_secure_code()

                    verification.increment_resend(commit=False)
                    verification.verification_code = secure_code
                    verification.set_expiry(
                        minutes=settings.DEFAULT_CODE_EXPIRY_IN_MINUTES
                        )

                    verification.save()

                    expiry_time = SecondsToTime(
                        verification.get_expiry_seconds()
                        ).format_to_human_readable()

                    transaction.on_commit(
                        lambda: send_confirmation_email_with_async(
                            username=user.username,
                            email=user.email,
                            subject="New Verification Code Request: Confirm Your Email Address",
                            verification_code=secure_code,
                            expiry_time=expiry_time,
                            )
                        )

                    return EmailVerificationResult(
                        outcome=EmailVerificationOutcome.CODE_SCHEDULED,
                        expiry_time=expiry_time
                    )

                case _:
                    logger.error(
                        "Unexpected verification status returned. "
                        "User ID: %s, Verification ID: %s, Status: %s",
                        user.pk,
                        verification.pk,
                        status,
                    )

                    return EmailVerificationResult(
                        outcome=EmailVerificationOutcome.ERROR
                    )
