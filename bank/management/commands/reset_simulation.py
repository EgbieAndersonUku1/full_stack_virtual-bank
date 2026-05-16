from django.core.management.base import BaseCommand
from django.db import transaction


from bank.models import Bank, BankAccount, SortCode, SortCodeAllocationStateLog


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        with transaction.atomic():

            SortCodeAllocationStateLog.objects.all().delete()
            BankAccount.objects.all().delete()
            SortCode.objects.all().delete()
            Bank.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS("Simulation successfully reset (banks deleted)")
        )