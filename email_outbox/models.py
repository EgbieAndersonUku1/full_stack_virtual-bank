from django.db import models
from uuid import uuid4

# Create your models here.
from django.db import models


# Keep them outside because constraint is throwing an error because it can't find them even though
# it is defined inside the EmailOutbox class
class EmailOutboxSupersededReason(models.TextChoices):
    REPLACED   = "replaced", "Replaced"
    CANCELLED  = "cancelled", "Cancelled"
    EXPIRED    = "expired", "Expired"

class EmailOutboxFailureType(models.TextChoices):
    TRANSIENT = "transient", "Transient"
    PERMANENT = "permanent", "Permanent"
    UNKNOWN   = "unknown", "Unknown"

class EmailOutboxPriority(models.IntegerChoices):
    CRITICAL = 1, "Critical"
    HIGH     = 2, "High"
    NORMAL   = 3, "Normal"

class EmailOutboxType(models.TextChoices):
    EMAIL_VERIFICATION = "ev", "Email verification"
    PASSWORD_RESET     = "pr", "Password reset"
    NOTIFICATION       = "n", "Notification"

class Status(models.TextChoices):
    PENDING    = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    SUPERSEDED = "SUPERSEDED", "Superseded"
    SENT       = "SENT", "Sent"
    FAILED     = "FAILED", "Failed"

class EmailOutbox(models.Model):

    id              = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    idempotency_key = models.UUIDField(default=uuid4, unique=True, editable=False)
    correlation_id  = models.UUIDField(null=True, blank=True, db_index=True)
    email_type      = models.CharField(max_length=30, choices=EmailOutboxType.choices)
    priority        = models.PositiveSmallIntegerField(choices=EmailOutboxPriority.choices, default=EmailOutboxPriority.NORMAL)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    verification    = models.ForeignKey("authentication.Verification", on_delete=models.PROTECT,
                                        related_name="email_outbox_requests",
                                        null=True,
                                        blank=True,
                                        )
    # Encrypted payload
    payload         = models.TextField(blank=True)
    payload_version = models.PositiveSmallIntegerField(default=1)
    status          = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    retry_of        = models.ForeignKey("self",
                                        on_delete=models.PROTECT,
                                        related_name="manual_retries",
                                        null=True,
                                        blank=True,
                                        )
    # Worker ownership
    claim_version               = models.PositiveBigIntegerField(default=0)
    processing_started_at       = models.DateTimeField(null=True, blank=True)
    processing_lease_expires_at = models.DateTimeField(null=True, blank=True)
    processing_deadline_at      = models.DateTimeField(null=True, blank=True)
    processing_worker_id        = models.UUIDField(null=True, blank=True)

    # Attempts and scheduling
    attempt_count               = models.PositiveIntegerField(default=0)
    last_attempt_at             = models.DateTimeField(null=True, blank=True)
    scheduled_at                = models.DateTimeField()
    next_attempt_at             = models.DateTimeField(null=True, blank=True)

    # Failure information
    failure_type                = models.CharField(
                                        max_length=10,
                                        choices=EmailOutboxFailureType.choices,
                                         null=True,
                                         blank=True
                                        )
    last_error                  = models.TextField(null=True, blank=True)
    failed_at                   = models.DateTimeField(null=True, blank=True)

    # Provider metadata
    provider                    = models.CharField(max_length=50, null=True, blank=True)
    provider_message_id         = models.CharField(max_length=255, null=True, blank=True)
    provider_response           = models.TextField(null=True, blank=True)
    provider_accepted_at        = models.DateTimeField(null=True, blank=True)
    sent_at                     = models.DateTimeField(null=True, blank=True)

    # Supersession
    superseded_at               = models.DateTimeField(null=True, blank=True)
    superseded_reason           = models.CharField(
                                    max_length=10,
                                    choices=EmailOutboxSupersededReason.choices,
                                    null=True,
                                    blank=True,
                                )

    superseded_by               = models.ForeignKey(
                                    "self",
                                    on_delete=models.PROTECT,
                                    related_name="superseded_requests",
                                    null=True,
                                    blank=True,
                                )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=Status.values),
                name="eo_valid_status",
            ),
            models.CheckConstraint(
                condition=models.Q(email_type__in=EmailOutboxType.values),
                name="eo_valid_email_type",
            ),
            models.CheckConstraint(
                condition=models.Q(priority__in=EmailOutboxPriority.values),
                name="eo_valid_priority",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(failure_type__isnull=True)
                     | models.Q(failure_type__in=EmailOutboxFailureType.values)
                ),
                name="eo_valid_failure_type",
            ),
            models.CheckConstraint(
                condition=models.Q(payload_version__gte=1),
                name="eo_valid_payload_version",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status=Status.SENT, sent_at__isnull=False)
                    | (~models.Q(status=Status.SENT) & models.Q(sent_at__isnull=True))
                ),
                name="eo_sent_timestamp_matches_status",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status=Status.FAILED, failed_at__isnull=False)
                    | (~models.Q(status=Status.FAILED) & models.Q(failed_at__isnull=True))
                ),
                name="eo_failed_timestamp_matches_status",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status=Status.SUPERSEDED, superseded_at__isnull=False)
                    | ( ~models.Q(status=Status.SUPERSEDED) & models.Q(superseded_at__isnull=True))
                ),
                name="eo_superseded_timestamp_matches_status",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        status=Status.PROCESSING,
                        processing_worker_id__isnull=False,
                        processing_started_at__isnull=False,
                        processing_lease_expires_at__isnull=False,
                        processing_deadline_at__isnull=False,
                    )
                    | (
                        ~models.Q(status=Status.PROCESSING)
                        & models.Q(
                            processing_worker_id__isnull=True,
                            processing_started_at__isnull=True,
                            processing_lease_expires_at__isnull=True,
                            processing_deadline_at__isnull=True,
                        )
                    )
                ),
                name="eo_processing_fields_match_status",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(status=Status.PROCESSING)
                    | (
                        models.Q(
                            processing_lease_expires_at__gt=models.F(
                                "processing_started_at"
                            )
                        )
                        & models.Q(
                            processing_deadline_at__gte=models.F(
                                "processing_lease_expires_at"
                            )
                        )
                    )
                ),
                name="eo_processing_time_order",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(attempt_count=0, last_attempt_at__isnull=True)
                    | (
                        models.Q(attempt_count__gt=0) & models.Q(last_attempt_at__isnull=False)
                    )
                ),
                name="eo_attempt_count_timestamp",
            ),

        models.CheckConstraint(
            condition=(models.Q(status=Status.PENDING) | models.Q(next_attempt_at__isnull=True)),
            name="eo_next_attempt_pending_only",
        ),

        models.CheckConstraint(
            condition=(
                models.Q(
                    failure_type__isnull=True,
                    last_error__isnull=True,
                )
                |
                models.Q(
                    failure_type__isnull=False,
                    last_error__isnull=False,
                )
            ),
            name="eo_failure_fields_together",
        ),

        models.CheckConstraint(
            condition=(
                models.Q(status__in=[Status.PENDING, Status.PROCESSING, Status.FAILED])
                |
                models.Q(
                    failure_type__isnull=True,
                    last_error__isnull=True,
                )
            ),
            name="eo_no_terminal_failure_info",
        ),

        models.CheckConstraint(
            condition=(
                (
                 models.Q(status__in=[Status.PENDING, Status.PROCESSING, Status.FAILED]
                 )
                  & ~models.Q(payload="")
                )

                |

                (
                 models.Q(status__in=[Status.SENT, Status.SUPERSEDED]) & models.Q(payload="")
                )
            ),
            name="eo_payload_matches_status",
        ),

        models.CheckConstraint(
            condition=(
                models.Q(provider__isnull=False)
                |
                models.Q(
                    provider_message_id__isnull=True,
                    provider_response__isnull=True,
                    provider_accepted_at__isnull=True,
                )
            ),
            name="eo_provider_metadata_requires_provider",
        ),

        models.CheckConstraint(
            condition=(
                ~models.Q(status=Status.SENT)
                |
                models.Q(
                    provider__isnull=False,
                    provider_accepted_at__isnull=False,
                )
            ),
            name="eo_sent_requires_provider_acceptance",
        ),

        models.CheckConstraint(
            condition=(
                models.Q(
                    status=Status.SUPERSEDED,
                    superseded_reason__isnull=False,
                )
                |
                (
                    ~models.Q(status=Status.SUPERSEDED)
                    & models.Q(superseded_reason__isnull=True)
                )
            ),
            name="eo_superseded_reason_matches_status",
        ),

        models.CheckConstraint(
            condition=(
                models.Q(status=Status.SUPERSEDED)
                |
                models.Q(superseded_by__isnull=True)
            ),
                name="eo_superseded_by_requires_status",
            ),


        models.CheckConstraint(
            condition=(
                models.Q(
                    superseded_reason=EmailOutboxSupersededReason.REPLACED,
                    superseded_by__isnull=False,
                )
                |
                (
                    ~models.Q(superseded_reason=EmailOutboxSupersededReason.REPLACED)
                    & models.Q(superseded_by__isnull=True)
                )
            ),
            name="eo_replaced_requires_successor",
        ),


        models.CheckConstraint(
            condition=(
                models.Q(superseded_by__isnull=True)
                |
                ~models.Q(superseded_by=models.F("id"))
            ),
            name="eo_no_self_supersession",
        ),


        models.CheckConstraint(
            condition=(
                (
                    models.Q(
                        email_type__in=[
                            EmailOutboxType.EMAIL_VERIFICATION,
                            EmailOutboxType.PASSWORD_RESET
                        ]
                    )
                    & models.Q(verification__isnull=False)
                )
                |
                (
                    models.Q(email_type=EmailOutboxType.NOTIFICATION)
                    & models.Q(verification__isnull=True)
                )
            ),
            name="eo_verification_matches_email_type",
        ),

        models.UniqueConstraint(
            fields=["verification"],
            condition=(
                models.Q(
                    status__in=[Status.PENDING, Status.PROCESSING]
                )
                & models.Q(verification__isnull=False)
            ),
            name="eo_unique_active_verification",
        ),

        models.UniqueConstraint(
            fields=["retry_of"],
            condition=models.Q(retry_of__isnull=False),
            name="eo_unique_direct_manual_retry",
        ),

        models.CheckConstraint(
            condition=(
                models.Q(last_error__isnull=True)
                | ~models.Q(last_error="")
            ),
            name="eo_last_error_nonempty",
        ),

        models.CheckConstraint(
            condition=(
                models.Q(provider__isnull=True)
                | ~models.Q(provider="")
            ),
            name="eo_provider_nonempty",
        ),


        ]

    def __str__(self):
        return f"{self.email_type} - " f"{self.status} ({self.pk})"
