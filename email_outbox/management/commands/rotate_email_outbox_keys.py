from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from email_outbox.payload_codec import rotate_payload


from email_outbox.models import EmailOutbox


class Command(BaseCommand):
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

    def handle(self, *args, **options):
        batch_size = options["batch_size"]

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

        self.stdout.write(
            "Rotation is not implemented yet. No records were modified."
        )

    def rotate_record(self, record_id):

        with transaction.atomic():
            record = (
                EmailOutbox.objects
                .select_for_update()
                .get(pk=record_id)
            )

            # The payload may have been cleared by a worker
            # while we were waiting for the row lock.
            if not record.payload:
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
