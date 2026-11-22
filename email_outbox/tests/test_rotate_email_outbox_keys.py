from django.test import TestCase
from cryptography.fernet import InvalidToken
from django.test import override_settings
from django.utils import timezone
from email_outbox.management.commands.rotate_email_outbox_keys import Command

from utils.security.encryption import Encryption
from email_outbox.models import EmailOutboxSupersededReason, EmailOutboxType, Status
from email_outbox.models import EmailOutbox



class EmailOutboxKeyRotationCommandTests(TestCase):
    """
    Tests for safely rotating encrypted email outbox
    payloads stored in the database.
    """

    def test_rotate_record_reencrypts_payload_with_primary_key(self):
        """Verify `Command.rotate_record` re-encrypts an outbox payload using the primary key.

        Ensures that when rotating a record encrypted with a deprecated key:
            - The payload is decrypted and re-encrypted under `EMAIL_OUTBOX_FERNET_KEY`.
            - The original plaintext data remains intact, and the old key can no longer decrypt it.
            - Record metadata (`status`, `attempt_count`, `updated_at`) is left unchanged.
        """

        old_key     = Encryption.generate_key()
        primary_key = Encryption.generate_key()

        payload = {
            "payload": "test payload"
        }

        old_token = Encryption(old_key).encrypt(payload)

        email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=old_token,
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        original_updated_at = email.updated_at

        self.assertEqual(EmailOutbox.objects.count(), 1)
        self.assertEqual(email.email_type, EmailOutboxType.NOTIFICATION)
        self.assertEqual(email.status, Status.PENDING)
        self.assertEqual(email.payload, old_token)

        # now we test the rotation
        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key],
        ):
            result = Command().rotate_record(email.pk)


        email.refresh_from_db()

        self.assertTrue(result)
        self.assertNotEqual(email.payload, old_token)
        self.assertEqual(email.status, Status.PENDING)
        self.assertEqual(email.attempt_count, 0)
        self.assertEqual(email.updated_at, original_updated_at)


        # test that the old key can no longer decrypt
        with self.assertRaises(InvalidToken):
            Encryption(old_key).decrypt(email.payload)

    def test_rotate_record_skips_empty_payload(self):

        old_key     = Encryption.generate_key()
        primary_key = Encryption.generate_key()

        email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload="",
            status=Status.SUPERSEDED,
            superseded_at=timezone.now(),
            superseded_reason=EmailOutboxSupersededReason.CANCELLED,
            scheduled_at=timezone.now(),
        )

        original_updated_at = email.updated_at

        email.refresh_from_db()
        self.assertFalse(email.payload)

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key],
            ):

            result = Command().rotate_record(email.pk)

        self.assertFalse(result)

        # assert that the payload is still an emtpy string and it wasn't updated
        self.assertEqual(email.payload, "")
        self.assertEqual(email.status, Status.SUPERSEDED)
        self.assertEqual(email.updated_at, original_updated_at)

    def test_rotate_record_preserves_payload_when_decryption_fails(self):

        primary_key = Encryption.generate_key()
        unknown_key = Encryption.generate_key()

        undecryptable_payload = Encryption(unknown_key).encrypt({"message": "Undecryptable payload"})

        email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=undecryptable_payload,
            status=Status.PENDING,
            scheduled_at=timezone.now(),
                )

        original_updated_at = email.updated_at
        email.refresh_from_db()

        self.assertTrue(email.payload)

        # check the configured keys cannot decrypt a stored token, the rotation command must not overwrite or erase that token.
        # This test verifies that the original database record remains unchanged when rotate_payload() raises InvalidToken.
        with override_settings(
                EMAIL_OUTBOX_FERNET_KEY=primary_key,
                EMAIL_OUTBOX_OLD_FERNET_KEYS=[],
            ):
            with self.assertRaises(InvalidToken):
                Command().rotate_record(email.pk)


        self.assertEqual(email.payload, undecryptable_payload)
        self.assertEqual(email.status, Status.PENDING)
        self.assertEqual(email.updated_at, original_updated_at)

    def test_get_record_batches_returns_all_eligible_records(self):

        emails = []

        for index in range(5):
            email = EmailOutbox.objects.create(
                email_type=EmailOutboxType.NOTIFICATION,
                payload=f"encrypted_payload_{index}",
                status=Status.PENDING,
                scheduled_at=timezone.now(),
            )
            emails.append(email)

        batches = list(Command().get_record_batches(batch_size=2))

        self.assertEqual(
            [len(batch) for batch in batches],
            [2, 2, 1],
        )

        returned_ids = [
            record_id
            for batch in batches
            for record_id in batch
        ]

        expected_ids = [email.pk for email in emails]

        self.assertCountEqual(returned_ids, expected_ids)
        self.assertEqual(len(returned_ids), len(set(returned_ids)))

    def test_get_record_batches_skips_empty_payloads(self):
        eligible_email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload="encrypted_payload",
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload="",
            status=Status.SUPERSEDED,
            superseded_at=timezone.now(),
            superseded_reason=EmailOutboxSupersededReason.CANCELLED,
            scheduled_at=timezone.now(),
        )

        batches = list(Command().get_record_batches(batch_size=2))

        self.assertEqual(batches, [[eligible_email.pk]])
