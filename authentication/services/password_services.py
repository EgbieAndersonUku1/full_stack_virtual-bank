

from authentication.models import User, Verification


class PasswordResetService:

    @classmethod
    def create_or_update_verification(cls, user: User) -> Verification:
        """Create or update a user's password-reset verification."""
        pass
