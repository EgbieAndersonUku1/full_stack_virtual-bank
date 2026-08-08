from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver

from bank.services.services import BankAccountCacheService
from card.models import BankCard
from card.services import CardDashboardServiceCache
from utils.safe_cache import delete_cache_with_retry, set_cache_with_retry



@receiver(pre_save, sender=BankCard)
def check_card_cache_update(sender, instance, **kwargs):

    if not instance.pk:
        instance._refresh_dashboard_cache = True
        return

    previous = sender.objects.get(pk=instance.pk)

    instance._refresh_dashboard_cache = (
        previous.is_active != instance.is_active
        or previous.show_in_dashboard != instance.show_in_dashboard
        or previous.balance != instance.balance
    )



@receiver(post_save, sender=BankCard)
def update_cache_after_card_model_update(sender, instance, **kwarg):

    if not getattr(instance, "_refresh_dashboard_cache", False):
        return

    refesh_cache(instance.user, id)




@receiver(post_delete, sender=BankCard)
def delete_cache_after_card_model_update(sender, instance, **kwargs):
    refesh_cache(instance.user, id)



def refesh_cache(user, id):
    current_account    = BankAccountCacheService.get_current_account(user=user)
    session_key        = CardDashboardServiceCache.construct_session_key(unique_id=user.id)

    dashboard_card_qs = BankCard.get_dashboard_cards(current_account)
    cards = list(dashboard_card_qs)

    set_cache_with_retry(session_key, cards)
