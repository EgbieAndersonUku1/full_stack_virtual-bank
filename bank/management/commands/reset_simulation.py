from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from bank.models import Bank, BankAccount, SortCode, SortCodeAllocationStateLog
from utils.safe_cache import delete_cache_with_retry, get_cache_with_retry


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        with transaction.atomic():

            SortCodeAllocationStateLog.objects.all().delete()
            BankAccount.objects.all().delete()
            SortCode.objects.all().delete()
            Bank.objects.all().delete()

        
        delete_cache_with_retry(key=settings.BANK_CACHE_KEY, retries=4, log_failures=True)
        self.stdout.write(
            self.style.SUCCESS("Simulation successfully reset (banks deleted)")
        )

        cache_data = get_cache_with_retry(key=settings.BANK_CACHE_KEY, retries=4, log_failures=True)
        
        if cache_data is None:
            self.stdout.write(
            self.style.SUCCESS("Successfully deleted bank simulation cache data")
        )
        else:
            self.stdout.write(self.style.ERROR("Failed to delete simulation cache data."))