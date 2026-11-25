import uuid

from django.test import TestCase
from cryptography.fernet import Fernet, InvalidToken
from django.test import override_settings
from django.utils import timezone
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError

from email_outbox.management.commands.rotate_email_outbox_keys import Command
from email_outbox.models import EmailOutboxSupersededReason, EmailOutboxType, Status
from email_outbox.models import EmailOutbox
from utils.custom_errors import InvalidEmailOutboxFernetKey
from utils.security.encryption import Encryption


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

    def test_command_rejects_invalid_batch_size(self):
        with self.assertRaisesMessage(
            CommandError,
            "--batch-size must be a positive integer.",
        ):
            call_command(
                "rotate_email_outbox_keys",
                batch_size=0,

                dry_run=True,
            )

    def test_dry_run_does_not_modify_encrypted_payloads(self):
        old_key     = Encryption.generate_key()
        primary_key = Encryption.generate_key()

        original_payload = {
            "recipient": "test@example.com",
            "subject": "Test notification",
        }

        encrypted_payload = Encryption(old_key).encrypt(original_payload)

        email = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=encrypted_payload,
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key],
        ):
            call_command(
                "rotate_email_outbox_keys",
                dry_run=True,

                batch_size=1,
            )

        email.refresh_from_db()

        self.assertEqual(email.payload, encrypted_payload)
        self.assertEqual(email.status, Status.PENDING)

    def test_command_rotates_records_across_multiple_batches(self):

        old_key     = Encryption.generate_key()
        primary_key = Encryption.generate_key()

        original_payload = {
            "recipient": "test@example.com",
            "subject": "Test notification",
        }

        records = []

        for _ in range(3):
            encrypted_payload = Encryption(old_key).encrypt(original_payload)
            record = EmailOutbox.objects.create(
                email_type=EmailOutboxType.NOTIFICATION,
                payload=encrypted_payload,
                status=Status.PENDING,
                scheduled_at=timezone.now(),
            )
            records.append(record)

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key],
        ):
            call_command(
                "rotate_email_outbox_keys",

                batch_size=2,
            )

            for record in records:
                record.refresh_from_db()

                decrypted_payload = Encryption(primary_key).decrypt(record.payload, to_json=True)

                self.assertEqual(
                    decrypted_payload,
                    original_payload,
                )

    def test_command_preserves_payload_when_rotation_fails(self):

        primary_key = Encryption.generate_key()
        unknown_key = Encryption.generate_key()

        encrypted_payload = Encryption(unknown_key).encrypt(
            {"recipient": "test@example.com"}
        )

        record = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=encrypted_payload,
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[],
        ):
            with self.assertRaises(CommandError):
                call_command(
                    "rotate_email_outbox_keys",
                    batch_size=1,
                )

        record.refresh_from_db()

        self.assertEqual(record.payload, encrypted_payload)
        self.assertEqual(record.status, Status.PENDING)

    def test_rotate_record_skips_payload_already_using_primary_key(self):
        primary_key = Encryption.generate_key()

        original_payload = {
            "recipient": "test@example.com",
            "subject": "Already encrypted with primary key",
        }

        encrypted_payload = Encryption(primary_key).encrypt(original_payload)

        record  = EmailOutbox.objects.create(
                email_type=EmailOutboxType.NOTIFICATION,
                payload=encrypted_payload,
                status=Status.PENDING,
                scheduled_at=timezone.now(),
                )

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[],
            ):

            result = Command().rotate_record(record.pk)

        record.refresh_from_db()

        self.assertFalse(result)
        self.assertEqual(record.payload, encrypted_payload)

    def test_command_skips_records_already_using_primary_key(self):
        primary_key = Encryption.generate_key()

        original_payload = {
            "recipient": "test@example.com",
            "subject": "Already using primary key",
        }

        encrypted_payload = Encryption(primary_key).encrypt(original_payload)

        record = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=encrypted_payload,
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[],
        ):
            call_command(
                "rotate_email_outbox_keys",
                batch_size=1,
            )

        record.refresh_from_db()

        self.assertEqual(record.payload, encrypted_payload)
        self.assertEqual(record.status, Status.PENDING)

    def test_command_skips_invalid_token_by_default_and_raises_at_end(self):
        primary_key = Encryption.generate_key()
        old_key     = Encryption.generate_key()
        unknown_key = Encryption.generate_key()
        payload     = {"test": "temporary payload"}

        record_before = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=Encryption(old_key).encrypt(payload),
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )
        unknown_record = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=Encryption(unknown_key).encrypt({"test": "unknown key"}),
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )
        record_after = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=Encryption(old_key).encrypt(payload),
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[primary_key, old_key],
        ):
            with self.assertRaises(CommandError):
                call_command("rotate_email_outbox_keys", batch_size=2)

        record_before.refresh_from_db()
        unknown_record.refresh_from_db()
        record_after.refresh_from_db()

        # Both valid records before and after the bad record should be rotated
        self.assertEqual(Encryption(primary_key).decrypt(record_before.payload, to_json=True), payload)
        self.assertEqual(Encryption(primary_key).decrypt(record_after.payload, to_json=True), payload)

        # Bad record remains untouched with its original key
        self.assertEqual(
            Encryption(unknown_key).decrypt(unknown_record.payload, to_json=True),
            {"test": "unknown key"},
        )

    def test_command_fail_fast_stops_immediately_on_invalid_token(self):

        primary_key = Encryption.generate_key()
        old_key = Encryption.generate_key()
        unknown_key = Encryption.generate_key()
        payload = {"test": "temporary payload"}

        record_before = EmailOutbox.objects.create(
            pk=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            email_type=EmailOutboxType.NOTIFICATION,
            payload=Encryption(old_key).encrypt(payload),
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )
        unknown_record = EmailOutbox.objects.create(
            pk=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            email_type=EmailOutboxType.NOTIFICATION,
            payload=Encryption(unknown_key).encrypt({"test": "unknown key"}),
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )
        record_after = EmailOutbox.objects.create(
            pk=uuid.UUID("00000000-0000-0000-0000-000000000003"),
            email_type=EmailOutboxType.NOTIFICATION,
            payload=Encryption(old_key).encrypt(payload),
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[primary_key, old_key],
        ):
            with self.assertRaises(CommandError):
                call_command("rotate_email_outbox_keys", batch_size=2, fail_fast=True)

        record_before.refresh_from_db()
        unknown_record.refresh_from_db()
        record_after.refresh_from_db()

        # Record before failure was committed
        self.assertEqual(Encryption(primary_key).decrypt(record_before.payload, to_json=True), payload)

        # Bad record and subsequent record were NOT rotated
        self.assertEqual(
            Encryption(unknown_key).decrypt(unknown_record.payload, to_json=True),
            {"test": "unknown key"},
        )
        self.assertEqual(Encryption(old_key).decrypt(record_after.payload, to_json=True), payload)

    def test_command_recovers_from_interrupted_rotation(self):
        """
        Verify that an interrupted email outbox key rotation can be
        safely resumed without modifying previously rotated payloads.

        This test covers three consecutive command executions:

        1. Initial rotation:

        - Successfully rotates the first record to the primary key.
        - Fails when the second record's encryption key is unavailable.
        - Preserves the successful rotation and the unrotated payload.

        2. Recovery:

        - Restores the missing key to the configured old keys.
        - Skips the previously rotated record.
        - Successfully rotates the remaining record.
        - Preserves the original plaintext.
        - Reports exactly one successful rotation.

        3. Idempotency:

        - Skips both records because they already use the primary key.
        - Preserves both encrypted tokens without modification.
        - Reports zero successful rotations.

        This will ensure that any interrupted key rotation operations are
        recoverable and repeatable without unnecessary re-encryption
        or loss of previously completed work.
        """
        primary_key = Encryption.generate_key()
        old_key     = Encryption.generate_key()
        unknown_key = Encryption.generate_key()

        original_payload = {"recipient": "test@example.com"}
        valid_payload   = Encryption(old_key).encrypt(original_payload)
        invalid_payload = Encryption(unknown_key).encrypt(original_payload)

        first_record = EmailOutbox.objects.create(
            pk=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            email_type=EmailOutboxType.NOTIFICATION,
            payload=valid_payload,
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        second_record = EmailOutbox.objects.create(
            pk=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            email_type=EmailOutboxType.NOTIFICATION,
            payload=invalid_payload,
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        # Simulate our first error, we delibrately remove the invalid key from the chain
        # so, MultiFernet can't find it, so throws an error when trying to re-encrypting
        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key]
            ):
            with self.assertRaises(CommandError):
                call_command(
                    "rotate_email_outbox_keys",
                    batch_size=1,
                )

        first_record.refresh_from_db()

        first_rotated_token  = first_record.payload

        self.assertNotEqual(first_rotated_token, valid_payload)
        self.assertEqual(Encryption(primary_key).decrypt(first_rotated_token, to_json=True), original_payload)
        self.assertEqual(second_record.payload, invalid_payload)

        output = StringIO()

        # We simulate recovering attempt by adding the unknown_key to chain so that MultiFernet can use it
        # It will decrypt it with the unknown key and encrypt with the primary_key
        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key, unknown_key],
            ):

            call_command(
                "rotate_email_outbox_keys",
                batch_size=1,
                stdout=output,
            )

        first_record.refresh_from_db()
        second_record.refresh_from_db()

        self.assertEqual(first_record.payload, first_rotated_token)
        self.assertNotEqual(second_record.payload, invalid_payload,)

        self.assertEqual(
            Encryption(primary_key).decrypt(second_record.payload, to_json=True),
            original_payload,
        )

        self.assertIn(
            "Successfully rotated 1 email outbox payload(s).",
            output.getvalue(),
        )
        second_rotated_token = second_record.payload

        output = StringIO()

        # rotate again but they should be no rotation
        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=[old_key, unknown_key],
        ):
            call_command(
                "rotate_email_outbox_keys",
                batch_size=1,
                stdout=output,
            )

        first_record.refresh_from_db()
        second_record.refresh_from_db()

        self.assertEqual(
            first_record.payload,
            first_rotated_token,
        )

        self.assertEqual(second_record.payload, second_rotated_token)

        self.assertIn(
            "Successfully rotated 0 email outbox payload(s).",
            output.getvalue(),
        )

    def test_rotate_record_rejects_invalid_old_key(self):
        """
        Ensure `rotate_record` validates old Fernet keys before short-circuiting
        on records already encrypted with the primary key, leaving the record's
        payload and status untouched if any configured key is invalid.
        """
        primary_key = Encryption.generate_key()

        encrypted_payload = Encryption(primary_key).encrypt(
           {"recipient": "test@example.com"}
        )

        record = EmailOutbox.objects.create(
            email_type=EmailOutboxType.NOTIFICATION,
            payload=encrypted_payload,
            status=Status.PENDING,
            scheduled_at=timezone.now(),
        )

        with override_settings(
            EMAIL_OUTBOX_FERNET_KEY=primary_key,
            EMAIL_OUTBOX_OLD_FERNET_KEYS=["invalid-old-key"]
        ):
            with self.assertRaises(InvalidEmailOutboxFernetKey):
                Command().rotate_record(record.pk)


        record.refresh_from_db()

        self.assertEqual(record.payload, encrypted_payload)
        self.assertEqual(record.status, Status.PENDING)
