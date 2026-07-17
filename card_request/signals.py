from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.conf import settings

from .errors import PendingCardRequestApplicationAlreadyExistsError
from .models import (CardRequestAgreement,
                     CardRequestApplication,

                     )
from utils.safe_cache import set_cache_with_retry, delete_cache_with_retry
from card_request.services import construct_card_application_session_key, CardRequestsApplicationCacheService



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



@receiver(pre_save, sender=CardRequestApplication)
def does_user_have_an_existing_pending_application(sender, instance, **kwargs):
    """
    Prevents a user from creating multiple pending card request applications.

    Before saving a card request application, this checks whether the user
    already has an existing pending application. If one exists, a
    PendingCardRequestApplicationAlreadyExistsError is raised.

    When an existing application changes from a pending state to another
    state (for example, accepted or rejected), the cached pending application
    status is removed. This ensures the user's application status page
    reflects the latest state without requiring stale cached data.

    Cache invalidation is used to prevent unnecessary database lookups when
    displaying the user's pending application status.
    """

    if instance._state.adding and CardRequestApplication.has_pending_application(instance.user):
        error_msg = _(
            "Cannot create a new card request application because user '{username}' already has a pending application."
        ).format(username=instance.user.username)

        raise PendingCardRequestApplicationAlreadyExistsError(error_msg)

    
    if not instance.pk:
        return

    previous = sender.objects.get(pk=instance.pk)

    cache_key = construct_card_application_session_key(instance.user.username)

    status_changed_to_pending = (
        previous.status != instance.status and
        previous.status != CardRequestApplication.Status.PENDING
        and instance.status == CardRequestApplication.Status.PENDING
    )
    if status_changed_to_pending:
        set_cache_with_retry(key=cache_key, value=CardRequestApplication.Status.PENDING)
        return

    delete_cache_with_retry(cache_key)


