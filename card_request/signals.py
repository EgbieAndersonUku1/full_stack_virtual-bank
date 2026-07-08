from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from .models import CardRequestAgreement
from utils.safe_cache import set_cache_with_retry, delete_cache_with_retry


@receiver(post_save, sender=CardRequestAgreement)
def update_card_request_cache(sender, instance, **kwargs):
    """
    Updates the cached card request agreement whenever a CardRequestAgreement
    instance is created or updated.

    The agreement data is stored as a lightweight dictionary rather than a
    Django model instance to avoid caching database objects and to ensure the
    cached value contains only the fields required by the card request flow.

    Args:
        sender: The model class that triggered the signal.
        instance: The CardRequestAgreement instance that was saved.
        **kwargs: Additional arguments provided by Django's post_save signal.
    """

    agreement_data = {
        "id": instance.pk,
        "title": instance.title,
        "terms_of_condition": instance.terms_of_condition,
    }

    set_cache_with_retry(
        key=settings.CARD_AGREEMENT_SESSION_KEY,
        value=agreement_data,
    )
    


@receiver(post_delete, sender=CardRequestAgreement)
def delete_card_request_cache(sender, instance, **kwargs):
    """
    Delete the cached card request agreement whenever a CardRequestAgreement
    is deleted.

    Args:
        sender: The model class that triggered the signal.
        instance: The CardRequestAgreement instance that was deleted.
        **kwargs: Additional arguments provided by Django's post_save signal.
    """

    delete_cache_with_retry(key=settings.CARD_AGREEMENT_SESSION_KEY)
    
  