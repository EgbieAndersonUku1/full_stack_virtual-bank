
from django.conf import settings

from .models import CardRequestAgreement
from utils.safe_cache import get_cache_with_retry, set_cache_with_retry



def get_card_request_agreement() -> dict[str, str] | None:
    """
    Retrieve the card request agreement.

    Returns the administrator-configured agreement from the cache when
    available. Otherwise, retrieves the agreement from the database,
    caches it, and returns it.

    Returns:
        dict[str, str] | None: The card request agreement, or ``None``
        if no custom agreement has been configured.
    """
    session_key            = settings.CARD_AGREEMENT_SESSION_KEY
    card_request_agreement = get_cache_with_retry(key=session_key)

    if card_request_agreement is None:
        
        agreement = CardRequestAgreement.objects.first()

        if agreement:
            card_request_agreement = {
                "id": agreement.id,
                "title": agreement.title,
                "terms_of_condition": agreement.terms_of_condition,
            }

            set_cache_with_retry(key=session_key, value=card_request_agreement)
            
    return card_request_agreement


