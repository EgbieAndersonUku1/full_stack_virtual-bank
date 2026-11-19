
import uuid
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
from authentication.models import Verification

from email_outbox.models import (
    EmailOutbox,
    EmailOutboxFailureType,
    EmailOutboxType,
    EmailOutboxPriority,
    EmailOutboxSupersededReason,
    Status
)

User = get_user_model()


class EmailOutboxSupersessionConstraintTests(TestCase):
    def _create_pending_notification(self):
        return EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            priority=EmailOutboxPriority.NORMAL,
            payload="encrypted_payload_data",
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

    def test_replaced_email_must_reference_successor(self):
        """
        REPLACED without superseded_by -> fails eo_replaced_requires_successor.
        """
        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=timezone.now(),
                    superseded_at=timezone.now(),
                    superseded_reason=EmailOutboxSupersededReason.REPLACED,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )
        self.assertEqual(constraint_name, "eo_replaced_requires_successor")

    def test_replaced_email_succeeds_with_successor(self):
        """
        REPLACED with superseded_by -> succeeds.
        """
        replacement = self._create_pending_notification()

        old_email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            priority=EmailOutboxPriority.NORMAL,
            payload="",
            status=Status.SUPERSEDED,
            scheduled_at=timezone.now(),
            superseded_at=timezone.now(),
            superseded_reason=EmailOutboxSupersededReason.REPLACED,
            superseded_by=replacement,
        )

        self.assertEqual(old_email.superseded_by, replacement)

    def test_non_replaced_superseded_email_forbids_successor(self):
        """
        CANCELLED or EXPIRED with superseded_by -> fails eo_replaced_requires_successor.
        """
        replacement = self._create_pending_notification()

        for reason in (
            EmailOutboxSupersededReason.CANCELLED,
            EmailOutboxSupersededReason.EXPIRED,
        ):
            with self.subTest(reason=reason):
                with self.assertRaises(IntegrityError) as caught:
                    with transaction.atomic():
                        EmailOutbox.objects.create(
                            email_type=EmailOutboxType.NOTIFICATION,
                            priority=EmailOutboxPriority.NORMAL,
                            payload="",
                            status=Status.SUPERSEDED,
                            scheduled_at=timezone.now(),
                            superseded_at=timezone.now(),
                            superseded_reason=reason,
                            superseded_by=replacement,
                        )

                constraint_name = getattr(
                    getattr(caught.exception.__cause__, "diag", None),
                    "constraint_name",
                    None,
                )
                self.assertEqual(constraint_name, "eo_replaced_requires_successor")

    def test_non_replaced_superseded_email_succeeds_without_successor(self):
        """
        CANCELLED or EXPIRED without superseded_by -> succeeds.
        """
        for reason in (
            EmailOutboxSupersededReason.CANCELLED,
            EmailOutboxSupersededReason.EXPIRED,
        ):
            with self.subTest(reason=reason):
                email = EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=timezone.now(),
                    superseded_at=timezone.now(),
                    superseded_reason=reason,
                )
                self.assertIsNone(email.superseded_by)


class EmailOutboxConstraintTests(TestCase):
    """
    Tests database-level check and unique constraints enforced on EmailOutbox
    when it is created.

    It also verifies that invalid email outbox records are rejected by the database,
    which ensures data integrity regardless of application-level validation.
    """

    def test_pending_email_cannot_have_empty_payload(self):
        """
        Ensure pending emails cannot be created with an empty payload.

        Verifies that the database raises an IntegrityError with the
        eo_payload_matches_status constraint when a pending email has
        an empty payload.
        """
        with self.assertRaises(IntegrityError) as caught:

            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.PENDING,
                    scheduled_at=timezone.now(),
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(constraint_name, "eo_payload_matches_status")

    def test_superseded_email_cannot_retain_payload(self):
        """
        Ensure superseded emails cannot retain a non-empty payload.

        Verifies that the database raises an IntegrityError with the
        eo_payload_matches_status constraint when a superseded email
        is created with a payload that should have been cleared.
        """

        with self.assertRaises(IntegrityError) as caught:

            with transaction.atomic():

                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="payload-that-should-be-cleared",
                    status=Status.SUPERSEDED,
                    scheduled_at=timezone.now(),
                    superseded_at=timezone.now(),
                    superseded_reason=EmailOutboxSupersededReason.CANCELLED,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(constraint_name, "eo_payload_matches_status")

    def test_replaced_email_must_reference_successor(self):
        """
        Ensure emails marked as replaced MUST reference a successor email.

        Verifies that the database raises an IntegrityError with the
        eo_replaced_requires_successor constraint when an email is marked
        as superseded for replacement without referencing its successor.
        """

        with self.assertRaises(IntegrityError) as caught:

            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=timezone.now(),
                    superseded_at=timezone.now(),
                    superseded_reason=EmailOutboxSupersededReason.REPLACED,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_replaced_requires_successor",
        )

    def test_duplicate_direct_manual_retry_is_rejected(self):
        """
        Ensure an original email cannot have multiple direct manual retries.

        Verifies that the database raises an IntegrityError with the
        eo_unique_direct_manual_retry constraint when a second retry is
        created for the same original email.

        Also confirms that the original email retains exactly one direct
        retry after the duplicate retry attempt is rejected.
        """
        now = timezone.now()

        original = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            priority=EmailOutboxPriority.NORMAL,
            payload="original-test-payload",
            status=Status.FAILED,
            scheduled_at=now,
            failed_at=now,
        )

        first_retry = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            priority=EmailOutboxPriority.NORMAL,
            payload="first-retry-payload",
            status=Status.PENDING,
            scheduled_at=now,
            retry_of=original,
        )

        self.assertIsNotNone(first_retry.pk)

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="second-retry-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    retry_of=original,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_unique_direct_manual_retry",
        )

        self.assertEqual(
            EmailOutbox.objects.filter(retry_of=original).count(),
            1,
        )


    def test_duplicate_active_verification_outbox_is_rejected(self):
        """
        Test that the database prevents multiple active email verification
        outbox entries from being associated with the same verification record.

        How it tests it?

            1. Creates an initial pending email verification outbox entry
            2. Then attempts to create a second active entry for the same verification.

        What must happen?

            The second insertion MUST raise an IntegrityError due to the
            `eo_unique_active_verification` database constraint.

        The test also verifies that the original outbox entry REMAINS intact and that
        only one active entry exists after the failed insertion.
        """

        user = User.objects.create_user(
            email="outbox-constraint-test@example.com",
            username="outbox_constraint_test",
            password="TestPassword123!",
        )

        now = timezone.now()

        verification = Verification.objects.create(
            user=user,
            verification_code="123456",
            description="Automated outbox constraint test",
            expiry_date=now + timedelta(minutes=15),
            verification_type=EmailOutboxType.EMAIL_VERIFICATION,
            status="P",
        )

        first_outbox = EmailOutbox.objects.create(
            email_type=EmailOutboxType.EMAIL_VERIFICATION,
            priority=EmailOutboxPriority.CRITICAL,
            payload="encrypted-test-payload-1",
            status=Status.PENDING,
            scheduled_at=now,
            verification=verification,
        )

        self.assertIsNotNone(first_outbox.pk)

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.EMAIL_VERIFICATION,
                    priority=EmailOutboxPriority.CRITICAL,
                    payload="encrypted-test-payload-2",
                    status=Status.PENDING,
                    scheduled_at=now,
                    verification=verification,
                )


        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_unique_active_verification",
        )

        self.assertEqual(
            EmailOutbox.objects.filter(
                verification=verification,
                status__in=["PENDING", Status.PROCESSING],
            ).count(),
            1,
        )


    def test_processing_email_cannot_duplicate_active_verification(self):
        """
        Test that a verification cannot have
         - multiple active email outbox entries
        even when the duplicate entry is created with a PROCESSING status.

        How it tests?

            1. Creates an initial PENDING email verification outbox entry
            2. then attempts to create a second entry for the same verification
            with a PROCESSING status and valid processing lease metadata.

        What must happen?

            The second insertion MUST raise an IntegrityError due to the
            `eo_unique_active_verification` database constraint to ensure that
            the uniqueness rule applies to both PENDING and PROCESSING entries.


        Finally, verifies that only one active outbox entry REMAINS associated
        with the verification record.
        """

        user = User.objects.create_user(
            email="processing-outbox-test@example.com",
            username="processing_outbox_test",
            password="TestPassword123!",
        )

        now = timezone.now()

        verification = Verification.objects.create(
            user=user,
            verification_code="654321",
            description="Processing uniqueness constraint test",
            expiry_date=now + timedelta(minutes=15),
            verification_type=EmailOutboxType.EMAIL_VERIFICATION,
            status="P",
        )

        EmailOutbox.objects.create(
            email_type=EmailOutboxType.EMAIL_VERIFICATION,
            priority=EmailOutboxPriority.CRITICAL,
            payload="encrypted-test-payload-1",
            status=Status.PENDING,
            scheduled_at=now,
            verification=verification,
        )

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.EMAIL_VERIFICATION,
                    priority=EmailOutboxPriority.CRITICAL,
                    payload="encrypted-test-payload-2",
                    status=Status.PROCESSING,
                    scheduled_at=now,
                    verification=verification,
                    processing_started_at=now,
                    processing_lease_expires_at=now + timedelta(minutes=1),
                    processing_deadline_at=now + timedelta(minutes=5),
                    processing_worker_id=uuid.uuid4(),
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_unique_active_verification",
        )

        self.assertEqual(
            EmailOutbox.objects.filter(
                verification=verification,
                status__in=[Status.PENDING, Status.PROCESSING],
            ).count(),
            1,
        )

    def test_sent_and_pending_emails_can_share_verification(self):
        """
        Test that historical SENT email outbox entries can co-exist with an
        active PENDING email outbox entry for the same verification record.

        What must happen?

        Both insertions MUSt succeed because the database uniqueness
        constraint `eo_unique_active_verification` applies only to active
        entries (PENDING and PROCESSING). What this means it  allows
        historical SENT entries to remain associated with the same verification.

        """

        user = User.objects.create_user(
            email="historical-outbox-test@example.com",
            username="historical_outbox_test",
            password="TestPassword123!",
        )

        now = timezone.now()

        verification = Verification.objects.create(
            user=user,
            verification_code="789123",
            description="Historical outbox constraint test",
            expiry_date=now + timedelta(minutes=15),
            verification_type=EmailOutboxType.EMAIL_VERIFICATION,
            status="P",
        )

        sent_email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.EMAIL_VERIFICATION,
            priority=EmailOutboxPriority.CRITICAL,
            payload="",
            status=Status.SENT,
            scheduled_at=now,
            verification=verification,
            provider="test-provider",
            provider_accepted_at=now,
            sent_at=now,
        )

        pending_email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.EMAIL_VERIFICATION,
            priority=EmailOutboxPriority.CRITICAL,
            payload="encrypted-test-payload",
            status=Status.PENDING,
            scheduled_at=now,
            verification=verification,
        )

        self.assertNotEqual(sent_email.pk, pending_email.pk)

        self.assertEqual(
            EmailOutbox.objects.filter(
                verification=verification,
            ).count(),
            2,
        )

        self.assertEqual(
            EmailOutbox.objects.filter(
                verification=verification,
                status__in=[Status.PENDING, Status.PROCESSING],
            ).count(),
            1,
        )

    def test_sent_email_cannot_retain_payload(self):
        """
        Test that once an email has been SENT by the email outbox it
        cannot retain its encrypted payload.

        This test verifies that:

        1. the expected database constraint rejects the invalid record
        2. Ensures that successfully sent emails do not retain sensitive payload data.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.SENT,
                    scheduled_at=now,
                    provider="test-provider",
                    provider_accepted_at=now,
                    sent_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_payload_matches_status",
        )


    def test_sent_email_requires_provider_acceptance(self):
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SENT,
                    scheduled_at=now,
                    provider="test-provider",
                    provider_accepted_at=None,
                    sent_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_sent_requires_provider_acceptance",
        )


    def test_sent_email_requires_sent_timestamp(self):
        """
        Test that an email cannot transition to SENT without a recorded
        provider acceptance timestamp.

        This ensures that an email cannot be marked as SENT without
        evidence of provider acceptance
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SENT,
                    scheduled_at=now,
                    provider="test-provider",
                    provider_accepted_at=now,
                    sent_at=None,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_sent_timestamp_matches_status",
        )


    def test_failed_email_requires_failed_timestamp(self):
        """
        Test that an email cannot be marked as FAILED without a recorded
        failure timestamp. Every email marked as FAILED must have a corresponding
        failed_at timestamp.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.FAILED,
                    scheduled_at=now,
                    failed_at=None,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_failed_timestamp_matches_status",
        )

    def test_failure_type_and_last_error_must_be_together(self):
        """
        Test that failure_type and last_error must either both be populated
        or both be NULL for an email outbox entry.

        An email outbox must never have an error description without a
        failure classification, or a failure classification without
        its corresponding error description.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.FAILED,
                    scheduled_at=now,
                    failed_at=now,
                    failure_type=None,
                    last_error="Test delivery failure",
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_failure_fields_together",
        )

    def test_sent_email_cannot_retain_failure_metadata(self):
        """
        Test that a SENT email outbox entry cannot retain failure metadata.

        Once an email reaches SENT, it must not retain any failure metadata.
        This prevents contradictory terminal states, where an email is recorded as
        successfully sent but still carries information indicating a
        previous delivery failure
        """

        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SENT,
                    scheduled_at=now,
                    provider="test-provider",
                    provider_accepted_at=now,
                    sent_at=now,
                    failure_type=EmailOutboxFailureType.TRANSIENT,
                    last_error="Previous delivery attempt failed",
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_no_terminal_failure_info",
        )

    def test_superseded_email_cannot_retain_failure_metadata(self):
        """
        Test that a SUPERSEDED email outbox entry cannot retain failure metadata.

        A SUPERSEDED email represents an email that has been replaced or cancelled,
        not one that has failed. When failure metadata is prevented it ensures
        that terminal states are unambiguous and that historical failure information
        doesn't conflict with the final outcome.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=now,
                    superseded_at=now,
                    superseded_reason=EmailOutboxSupersededReason.CANCELLED,
                    failure_type=EmailOutboxFailureType.TRANSIENT,
                    last_error="Previous delivery attempt failed",
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_no_terminal_failure_info",
        )

    def test_processing_email_requires_worker_id(self):
        """
        Test that an email marked as PROCESSING must have an assigned worker ID.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PROCESSING,
                    scheduled_at=now,
                    processing_started_at=now,
                    processing_lease_expires_at=now + timedelta(minutes=1),
                    processing_deadline_at=now + timedelta(minutes=5),
                    processing_worker_id=None,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_processing_fields_match_status",
        )


    def test_processing_lease_must_expire_after_start(self):
        """
        Test that a processing lease expiry timestamp must be later than
        the processing start timestamp.

        Verifies that a processing lease must always expire after processing begins.
        This ensures workers have a valid lease window and prevents invalid timestamps
        from undermining lease expiry, worker recovery and concurrent processing safeguards.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PROCESSING,
                    scheduled_at=now,
                    processing_started_at=now,
                    processing_lease_expires_at=now - timedelta(minutes=1),
                    processing_deadline_at=now + timedelta(minutes=5),
                    processing_worker_id=uuid.uuid4(),
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_processing_time_order",
        )

    def test_processing_deadline_cannot_precede_lease_expiry(self):
        """
        Test that the processing deadline cannot occur before the processing
        lease expiry timestamp.

        Verifies that the overall processing deadline must not precede the
        worker's lease expiry. This preserves a consistent processing window,
        allowing the worker's lease to remain valid within the permitted
        lifetime of the processing attempt.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PROCESSING,
                    scheduled_at=now,
                    processing_started_at=now,
                    processing_lease_expires_at=now + timedelta(minutes=5),
                    processing_deadline_at=now + timedelta(minutes=2),
                    processing_worker_id=uuid.uuid4(),
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_processing_time_order",
        )

    def test_pending_email_cannot_retain_processing_fields(self):
        """
        Test that an email marked as PENDING cannot retain processing-related
        metadata from a previous processing attempt.

        Verifies that a PENDING email must not retain worker assignments or
        processing lease information. This prevents stale processing metadata
        from interfering with subsequent worker assignment and also ensures
        a clean transition between PENDING and PROCESSING states.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    processing_started_at=now,
                    processing_lease_expires_at=now + timedelta(minutes=1),
                    processing_deadline_at=now + timedelta(minutes=5),
                    processing_worker_id=uuid.uuid4(),
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_processing_fields_match_status",
        )

    def test_processing_email_cannot_retain_next_attempt_timestamp(self):
        """
        Test that an email marked as PROCESSING cannot have a next_attempt_at
        timestamp assigned.

        Verifies that An email currently being processed must not simultaneously
        have a scheduled retry timestamp. Retry scheduling belongs only to the PENDING state,
        preventing conflicting processing and retry instructions.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PROCESSING,
                    scheduled_at=now,
                    processing_started_at=now,
                    processing_lease_expires_at=now + timedelta(minutes=1),
                    processing_deadline_at=now + timedelta(minutes=5),
                    processing_worker_id=uuid.uuid4(),
                    next_attempt_at=now + timedelta(minutes=10),
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_next_attempt_pending_only",
        )


    def test_pending_email_can_have_next_attempt_timestamp(self):
        """
        Test that a PENDING email can have a scheduled next_attempt_at timestamp.

        Verifies that a PENDING email is allowed to retain a future retry timestamp.
        This ensures the outbox can schedule delivery retries without prematurely moving
        the email into the PROCESSING state
        """
        now          = timezone.now()
        next_attempt = now + timedelta(minutes=10)

        email = EmailOutbox.objects.create(
             email_type=EmailOutboxType.NOTIFICATION,
             priority=EmailOutboxPriority.NORMAL,
             payload="encrypted-test-payload",
             status=Status.PENDING,
             scheduled_at=now,
             next_attempt_at=next_attempt,
        )

        email.refresh_from_db()
        self.assertEqual(email.status, Status.PENDING)
        self.assertEqual(email.next_attempt_at, next_attempt)

    def test_positive_attempt_count_requires_last_attempt_timestamp(self):
        """
        Test that an email with a positive attempt_count must have a recorded
        last_attempt_at timestamp.

        Verifies that very recorded delivery attempt must have a corresponding timestamp.
        This keeps retry tracking accurate and ensures you can reliably
        determine when an email was last attempted.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    attempt_count=1,
                    last_attempt_at=None,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_attempt_count_timestamp",
        )


    def test_zero_attempt_count_cannot_have_last_attempt_timestamp(self):
        """
        Test that an email with an attempt_count of zero cannot have a
        last_attempt_at timestamp recorded.

        Verifies that an email cannot have a recorded last-attempt timestamp
        when its attempt count is zero. You cannot have a last-attempt
        timestamp if not attempts have ever been made.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    attempt_count=0,
                    last_attempt_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_attempt_count_timestamp",
        )

    def test_positive_attempt_count_with_timestamp_is_allowed(self):
        """
        Test that an email with a positive attempt_count can have a
        corresponding last_attempt_at timestamp.

        Verifies that a pending email that has already undergone a delivery
        attempt can retain both its positive attempt count and corresponding timestamp

        """
        now = timezone.now()

        email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            priority=EmailOutboxPriority.NORMAL,
            payload="encrypted-test-payload",
            status=Status.PENDING,
            scheduled_at=now,
            attempt_count=1,
            last_attempt_at=now,
        )

        email.refresh_from_db()

        self.assertEqual(email.status, Status.PENDING)
        self.assertEqual(email.attempt_count, 1)
        self.assertEqual(email.last_attempt_at, now)

    def test_zero_attempt_count_without_timestamp_is_allowed(self):
        """
        Test that an email with an attempt_count of zero can have a NULL
        last_attempt_at timestamp.

        Verifies that newly queued emails can start with zero delivery
        attempts and no attempt timestamp. This ensures the outbox correctly
        represents emails that have not yet been processed
        """
        now = timezone.now()

        email = EmailOutbox.objects.create(
             email_type=EmailOutboxType.NOTIFICATION,
             priority=EmailOutboxPriority.NORMAL,
             payload="encrypted-test-payload",
             status=Status.PENDING,
             scheduled_at=now,
             attempt_count=0,
             last_attempt_at=None,
        )

        email.refresh_from_db()

        self.assertEqual(email.status, Status.PENDING)
        self.assertEqual(email.attempt_count, 0)
        self.assertIsNone(email.last_attempt_at)

    def test_payload_version_zero_is_rejected(self):
        """
        Test that an email outbox entry cannot have a payload_version of zero.

        Verifies that every outbox payload must have a valid version.
        This prevents invalid version identifiers from entering the database
        and helps ensure the correct encryption/decryption logic is applied when
        processing queued emails.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                     email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    payload_version=0,
                   status=Status.PENDING,
                    scheduled_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_valid_payload_version",
        )

    def test_payload_version_one_is_allowed(self):
        """
        Test that an email outbox entry can be created with payload_version 1.
        """
        now = timezone.now()

        email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            priority=EmailOutboxPriority.NORMAL,
            payload="encrypted-test-payload",
            payload_version=1,
            status=Status.PENDING,
            scheduled_at=now,
        )

        email.refresh_from_db()

        self.assertEqual(email.status, Status.PENDING)
        self.assertEqual(email.payload_version, 1)

    def test_payload_version_two_is_allowed(self):
        """
        Test that an email outbox entry can be created with payload_version 2.

        This ensures that the outbox supports storing and retrieving
        emails using newer payload formats without violating database integrity.

        """
        now = timezone.now()

        email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            priority=EmailOutboxPriority.NORMAL,
            payload="encrypted-test-payload",
            payload_version=2,
            status=Status.PENDING,
            scheduled_at=now,
        )

        email.refresh_from_db()

        self.assertEqual(email.status, Status.PENDING)
        self.assertEqual(email.payload_version, 2)

    def test_provider_message_id_requires_provider(self):
        """
        Test that a provider_message_id cannot be stored without an associated
        email provider.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    provider=None,
                    provider_message_id="test-message-123",
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_provider_metadata_requires_provider",
        )

    def test_provider_acceptance_timestamp_requires_provider(self):
        """
        Test that a provider_accepted_at timestamp cannot be recorded without
        an associated email provider.

        Verifies that a provider acceptance timestamp must always
        be associated with an identified email provider. This prevents
        ambiguous delivery records and always ensures that any provider acceptance
        can always be reliably traced and audited
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    provider=None,
                    provider_accepted_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_provider_metadata_requires_provider",
        )

    def test_provider_response_requires_provider(self):
        """
        Test that a provider response cannot be recorded without an
        associated email provider.

        Verifies that that provider_response cannot be stored unless
        an email provider is identified. This prevents provider-specific
        response data from becoming detached from the provider
        that returned it.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    provider=None,
                    provider_response="Provider accepted request",
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_provider_metadata_requires_provider",
        )

    def test_empty_provider_name_is_rejected(self):
        """
        Test that an empty provider name is rejected.

        Verifies that an empty string cannot be stored as a provider name.
        This ensures that provider metadata are meaningful and prevents outbox
        from records which appears to have a provider assigned but
        the value is actually blank.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    provider="",
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_provider_nonempty",
        )

    def test_empty_last_error_is_rejected(self):
        """
        Test that an empty last_error value is rejected.

        This prevents failed email records from storing an
        empty error message. This helps ensure that any failure that
        is recorded contain meaningful diagnostic information
        for troubleshooting and auditing.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.FAILED,
                    scheduled_at=now,
                    failed_at=now,
                    failure_type=EmailOutboxFailureType.TRANSIENT,
                    last_error="",
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_last_error_nonempty",
        )

    def test_invalid_priority_is_rejected(self):
        """
        Test that an unsupported priority value is rejected.

        Valid priorities are:

        class EmailOutboxPriority(models.IntegerChoices):
            CRITICAL = 1, "Critical"
            HIGH     = 2, "High"
            NORMAL   = 3, "Normal"

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=4,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_valid_priority",
        )

    def test_zero_priority_is_rejected(self):
        """
        Test that a priority value of zero is rejected.

        Valid priorities are:

        class EmailOutboxPriority(models.IntegerChoices):
            CRITICAL = 1, "Critical"
            HIGH     = 2, "High"
            NORMAL   = 3, "Normal"

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=0,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_valid_priority",
        )

    def test_invalid_email_type_is_rejected(self):
        """
        Test that an unsupported email type is rejected.

        Valid email types are:

        class EmailOutboxType(models.TextChoices):
            EMAIL_VERIFICATION = "ev", "Email verification"
            PASSWORD_RESET     = "pr", "Password reset"
            NOTIFICATION       = "n", "Notification"
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type="marketing",
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_valid_email_type",
        )

    def test_invalid_status_is_rejected(self):
        """
        Test that an unsupported email status is rejected.

        Valid Status choices are:

        class Status(models.TextChoices):
            PENDING    = "PENDING", "Pending"
            PROCESSING = "PROCESSING", "Processing"
            SUPERSEDED = "SUPERSEDED", "Superseded"
            SENT       = "SENT", "Sent"
            FAILED     = "FAILED", "Failed"
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status="QUEUED",
                    scheduled_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertIn(
            constraint_name,
            {
                "eo_valid_status",
                "eo_payload_matches_status",
            },
        )

    def test_invalid_failure_type_is_rejected(self):
        """
        Test that an unsupported failure type is rejected.

        Valid Failure types are:

        class EmailOutboxFailureType(models.TextChoices):
            TRANSIENT = "transient", "Transient"
            PERMANENT = "permanent", "Permanent"
            UNKNOWN   = "unknown", "Unknown"
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.FAILED,
                    scheduled_at=now,
                    failed_at=now,
                    failure_type="invalid",
                    last_error="Test delivery failure",
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_valid_failure_type",
        )

    def test_notification_email_cannot_reference_verification(self):
        """
        Test that a NOTIFICATION email cannot reference a verification record.

        Verifies that a NOTIFICATION email cannot be linked to a verification record.
        This preserves the relationship between email types and their
        associated verification data and prevents unrelated
        notification messages from referencing verification workflows.
        """
        now = timezone.now()

        user = User.objects.create_user(
            email="notification-verification-test@example.com",
            username="notification_verification_test",
            password="TestPassword123!",
        )

        verification = Verification.objects.create(
            user=user,
            verification_code="123456",
            description="Notification verification constraint test",
            expiry_date=now + timedelta(minutes=15),
            verification_type=EmailOutboxType.EMAIL_VERIFICATION,
            status="P",
        )

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    verification=verification,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_verification_matches_email_type",
        )

    def test_email_verification_requires_verification_record(self):
        """
        Test that an EMAIL_VERIFICATION email must reference a verification
        record.

        It ensures that an EMAIL_VERIFICATION outbox entry cannot
        exist without an associated verification record.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.EMAIL_VERIFICATION,
                    priority=EmailOutboxPriority.CRITICAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    verification=None,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_verification_matches_email_type",
        )

    def test_password_reset_requires_verification_record(self):
        """
        Test that a PASSWORD_RESET email must reference a verification
        record.

        It ensures that a PASSWORD_RESET outbox entry cannot be created
        without an associated verification record,
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.PASSWORD_RESET,
                    priority=EmailOutboxPriority.CRITICAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    verification=None,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_verification_matches_email_type",
        )


    def test_superseded_email_requires_reason(self):
        """
        Test that a SUPERSEDED email must have an associated supersession
        reason.

        It ensures that an email cannot be marked as SUPERSEDED without
        recording why it was superseded. This preserves the context
        needed to understand and audit supersession events.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=now,
                    superseded_at=now,
                    superseded_reason=None,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_superseded_reason_matches_status",
        )

    def test_pending_email_cannot_have_supersession_reason(self):
        """
        Test that a PENDING email cannot have a supersession reason.

        It ensures that pending emails cannot carry supersession metadata.
        A supersession reason is only valid when an email has actually been
        marked as SUPERSEDED.
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    superseded_reason=EmailOutboxSupersededReason.CANCELLED,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_superseded_reason_matches_status",
        )

    def test_email_cannot_supersede_itself(self):
        """
        Test that an email outbox entry cannot reference itself as the
        email that superseded it.

        It prevents an email from being recorded as its own replacement.
        This avoids invalid self-referencing relationships and keeps
        the email supersession history consistent.
        """
        now       = timezone.now()
        outbox_id = uuid.uuid4()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    id=outbox_id,
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=now,
                    superseded_at=now,
                    superseded_reason=EmailOutboxSupersededReason.REPLACED,
                    superseded_by_id=outbox_id,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_no_self_supersession",
        )

    def test_superseded_email_requires_timestamp(self):
        """
        Test that a SUPERSEDED email must have a supersession timestamp.

        It ensures that every email marked as SUPERSEDED has a timestamp recording
        when the supersession occurred. This keeps email lifecycle history
        complete and auditable.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=now,
                    superseded_at=None,
                    superseded_reason=EmailOutboxSupersededReason.CANCELLED,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_superseded_timestamp_matches_status",
        )

    def test_pending_email_cannot_have_superseded_timestamp(self):
        """
        Test that a PENDING email cannot have a supersession timestamp.

        It ensures that pending emails cannot carry a supersession timestamp.
        Supersession timestamps are reserved for emails actually marked
        as SUPERSEDED
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    superseded_at=now,
                    superseded_reason=None,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_superseded_timestamp_matches_status",
        )

    def test_pending_email_cannot_reference_successor(self):
        now = timezone.now()

        successor = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            priority=EmailOutboxPriority.NORMAL,
            payload="encrypted-successor-payload",
            status=Status.PENDING,
            scheduled_at=now,
        )

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type="notification",
                    priority=3,
                    payload="encrypted-test-payload",
                    status="PENDING",
                    scheduled_at=now,
                    superseded_by=successor,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_superseded_by_requires_status",
        )

    def test_sent_email_cannot_have_supersession_reason(self):
        """
        Test that a SENT email cannot have a supersession reason.

        It ensures that a SENT email cannot retain a supersession reason.
        Supersession metadata belongs only to emails marked as SUPERSEDED,
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SENT,
                    scheduled_at=now,
                    provider="test-provider",
                    provider_accepted_at=now,
                    sent_at=now,
                    superseded_reason=EmailOutboxSupersededReason.CANCELLED,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_superseded_reason_matches_status",
        )

    def test_sent_email_cannot_have_superseded_timestamp(self):
        """
        Test that a SENT email cannot have a supersession timestamp.
        It ensures that a SENT email cannot retain a supersession timestamp.
        Supersession timestamps are reserved for emails marked as SUPERSEDED
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SENT,
                    scheduled_at=now,
                    provider="test-provider",
                    provider_accepted_at=now,
                    sent_at=now,
                    superseded_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_superseded_timestamp_matches_status",
        )

    def test_failed_email_cannot_have_sent_timestamp(self):
        """
        Test that a FAILED email cannot have a sent timestamp.
        It ensures that a FAILED email cannot have a sent_at timestamp.
        This prevents contradictory lifecycle information, where an
        email is simultaneously recorded as failed and sent.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.FAILED,
                    scheduled_at=now,
                    failed_at=now,
                    sent_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_sent_timestamp_matches_status",
        )

    def test_pending_email_cannot_have_failed_timestamp(self):
        """
        Test that a PENDING email cannot have a failure timestamp.

        It ensures that a PENDING email cannot have a failure timestamp.
        This prevents pending emails from carrying failure metadata before they
        have actually entered the FAILED state.It ensures that a PENDING email cannot have a failure timestamp.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    failed_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_failed_timestamp_matches_status",
        )

    def test_pending_email_cannot_have_sent_timestamp(self):
        """
        Test that a PENDING email cannot have a sent timestamp.
        It ensures that a PENDING email cannot have a sent_at timestamp.
        This prevents an email from carrying sent-state metadata before
        it has actually reached the SENT status.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="encrypted-test-payload",
                    status=Status.PENDING,
                    scheduled_at=now,
                    sent_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_sent_timestamp_matches_status",
        )

    def test_sent_email_cannot_have_failed_timestamp(self):
        """
        Test that a SENT email cannot have a failure timestamp
        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SENT,
                    scheduled_at=now,
                    provider="test-provider",
                    provider_accepted_at=now,
                    sent_at=now,
                    failed_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_failed_timestamp_matches_status",
        )

    def test_superseded_email_cannot_have_sent_timestamp(self):
        """
        Test that a SUPERSEDED email cannot have a sent timestamp.
        It ensures that a SUPERSEDED email cannot carry a sent timestamp.
        This prevents superseded emails from retaining delivery metadata
        that should only belong to emails marked as SENT.

        """
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=now,
                    superseded_at=now,
                    superseded_reason="cancelled",
                    sent_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_sent_timestamp_matches_status",
        )


    def test_superseded_email_cannot_have_failed_timestamp(self):
        now = timezone.now()

        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                EmailOutbox.objects.create(
                    email_type=EmailOutboxType.NOTIFICATION,
                    priority=EmailOutboxPriority.NORMAL,
                    payload="",
                    status=Status.SUPERSEDED,
                    scheduled_at=now,
                    superseded_at=now,
                    superseded_reason=EmailOutboxSupersededReason.CANCELLED,
                    failed_at=now,
                )

        constraint_name = getattr(
            getattr(caught.exception.__cause__, "diag", None),
            "constraint_name",
            None,
        )

        self.assertEqual(
            constraint_name,
            "eo_failed_timestamp_matches_status",
        )
