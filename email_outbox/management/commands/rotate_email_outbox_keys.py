from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from cryptography.fernet import InvalidToken

from django.conf import settings

from email_outbox.payload_codec import rotate_payload




from email_outbox.models import EmailOutbox
from utils.security.encryption import Encryption


class Command(BaseCommand):
    MAX_DISPLAYED_ERRORS = 20
    help = "Rotate encrypted email outbox payloads to the current primary Fernet key."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Count eligible payloads without modifying the database.",
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Maximum number of outbox records to process per batch (default: 100).",
        )

        parser.add_argument(
            "--fail-fast",
            action="store_true",
            help="Stop immediately on the first InvalidToken instead of skipping failed records.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        fail_fast  = options["fail_fast"]

        if batch_size < 1:
            raise CommandError(
                "--batch-size must be a positive integer."
            )

        eligible_count = (
            EmailOutbox.objects
            .exclude(payload="")
            .count()
        )

        if options["dry_run"]:
            self.stdout.write(
                f"Dry run: {eligible_count} email outbox payload(s) eligible for rotation."
            )
            return

        if eligible_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "No encrypted email outbox payloads require processing."
                )
            )
            return

        rotated_count = 0
        failed_ids = []

        for record_ids in self.get_record_batches(batch_size):
            for record_id in record_ids:
                try:
                    if self.rotate_record(record_id):
                        rotated_count += 1
                except InvalidToken as exc:
                    if fail_fast:
                        raise CommandError(
                            f"Aborted: Failed to rotate EmailOutbox pk={record_id} due to InvalidToken."
                        ) from exc

                    failed_ids.append(record_id)
                    if len(failed_ids) <= self.MAX_DISPLAYED_ERRORS:
                        self.stderr.write(
                            self.style.ERROR(
                                f"Failed to rotate EmailOutbox pk={record_id}: InvalidToken"
                            )
                        )
                    elif len(failed_ids) == self.MAX_DISPLAYED_ERRORS + 1:
                        self.stderr.write(
                            self.style.WARNING(
                                f"More than {self.MAX_DISPLAYED_ERRORS} InvalidToken errors encountered; suppressing further individual error logs."
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully rotated {rotated_count} email outbox payload(s)."
            )
        )

        if failed_ids:
            sample_ids = failed_ids[: self.MAX_DISPLAYED_ERRORS]
            suffix = (
                f" (showing first {self.MAX_DISPLAYED_ERRORS})"
                if len(failed_ids) > self.MAX_DISPLAYED_ERRORS
                else ""
            )
            raise CommandError(
                f"Failed to rotate {len(failed_ids)} record(s) due to InvalidToken{suffix}: {sample_ids}"
            )

    def rotate_record(self, record_id):

        with transaction.atomic():
            record = (
                EmailOutbox.objects
                .select_for_update()
                .get(pk=record_id)
            )

            if not record.payload:
                return False

            primary_fernet = Encryption(settings.EMAIL_OUTBOX_FERNET_KEY)

            try:
                primary_fernet.decrypt(record.payload)
            except InvalidToken:
                # The primary key cannot decrypt this token.
                # Attempt rotation using the configured old keys.
                pass
            else:
                # Already encrypted with the primary key.
                # No database update is necessary.
                return False

            rotated_payload = rotate_payload(record.payload)

            # Update only the encrypted payload.
            EmailOutbox.objects.filter(pk=record_id).update(
                payload=rotated_payload
            )

            return True

    def get_record_batches(self, batch_size):
        last_id = None

        while True:
            queryset = (
                EmailOutbox.objects
                .exclude(payload="")
                .order_by("pk")
            )

            if last_id is not None:
                queryset = queryset.filter(pk__gt=last_id)

            record_ids = list(
                queryset.values_list("pk", flat=True)[:batch_size]
            )

            if not record_ids:
                break

            yield record_ids

            last_id = record_ids[-1]

