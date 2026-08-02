from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver

from bank.services import BankAccountCacheService
from card.models import BankCard
from card.services import CardDashboardServiceCache
from utils.safe_cache import delete_cache_with_retry, set_cache_with_retry



@receiver(post_save, sender=BankCard)
def update_cache_after_card_model_update(sender, instance, **kwarg):

    pk = instance.pk

    if not pk:
        return

    previous = sender.objects.get(pk=pk)

    should_update_cache = (previous.is_active != instance.is_active
                     or previous.show_in_dashboard != instance.show_in_dashboard
                     or previous.balance != instance.balance

                     )


    if should_update_cache:

        bank_account    = BankAccountCacheService.get_accounts(user=instance.user)
        current_account = bank_account.first()

        session_key     = CardDashboardServiceCache.construct_session_key(unique_id=instance.user.id)
        dashboard_cards = BankCard.get_dashboard_cards(current_account)

        if dashboard_cards:
            cards = list(dashboard_cards)
            set_cache_with_retry(session_key, cards)



@receiver(post_delete, sender=BankCard)
def delete_cache_after_card_model_update(sender, instance, **kwargs):
    session_key  = CardDashboardServiceCache.construct_session_key(unique_id=instance.user.id)
    delete_cache_with_retry(session_key)
