from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from user_profile.models import UserProfile
from utils.safe_cache import get_cache_or_set


User = get_user_model()


class ProfileCacheService:
    CACHE_TIMEOUT = 300

    @classmethod
    def get_user_profile(cls, user: User):
        
        if not isinstance(user, User):
            raise TypeError( _("The user is not a User instance. Expected a user instance got object with type %s")% type(user).__name__)
        
        profile = get_cache_or_set(key=f"profile-{user.id}", 
                         value_or_func=lambda: UserProfile.get_profile_by_user(user=user),
                         ttl=cls.CACHE_TIMEOUT,
                         )
        return profile