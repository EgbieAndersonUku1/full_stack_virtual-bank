from cryptography.fernet import Fernet


class Encryption:
    """
    Provides string encryption and decryption using Fernet symmetric encryption.

    The class validates input types and delegates encryption, decryption,
    and key validation to the Fernet implementation.

    A valid Fernet encryption key must be supplied during initialisation.
    The same key must be retained to decrypt previously encrypted data.
    """

    def __init__(self, encryption_key: str) -> None:
        if not isinstance(encryption_key, str):
            error_msg = (
                f"The encryption key is not a string. "
                f"Expected a string got {type(encryption_key).__name__}"
            )
            raise TypeError(error_msg)

        self._fernet = Fernet(encryption_key.encode())

    def _validate(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(
                f"Expected the value to be a string. Got type {type(value).__name__}"
            )

    @staticmethod
    def generate_key():
        """
        Generate a valid Fernet encryption key.

        Generate this key once during application setup and store it securely.
        Do not generate a new key every time the application starts, as
        previously encrypted data would no longer be decryptable.

        For Django applications, store the generated key in an environment
        variable and load it through settings.

        Example:

            # Generate once during initial setup:
            encryption_key = Encryption.generate_key()

            # Store the key in your .env file:
            EMAIL_OUTBOX_ENCRYPTION_KEY=<generated-key>

            # Load it in settings.py:
            EMAIL_OUTBOX_ENCRYPTION_KEY = os.getenv(
                "EMAIL_OUTBOX_ENCRYPTION_KEY"
            )

            # Use it in your application:
            encryption = Encryption(settings.EMAIL_OUTBOX_ENCRYPTION_KEY)
            ciphertext = encryption.encrypt("Sensitive email payload")

        Returns:
            str: A URL-safe Base64-encoded Fernet encryption key.
        """
        return Fernet.generate_key().decode()

    def encrypt(self, plaintext: str) -> str:
        self._validate(plaintext)
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        self._validate(encrypted_text)
        return self._fernet.decrypt(encrypted_text.encode()).decode()









