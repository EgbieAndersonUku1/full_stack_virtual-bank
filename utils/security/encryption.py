import json

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

    def _validate(self, value: str | dict) -> None:

        if not isinstance(value, (str, dict)):
                raise TypeError(
                    f"Expected the value to be a string or dict. Got type {type(value).__name__}"
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

    def encrypt(self, plaintext: str | dict) -> str:

        self._validate(plaintext)

        if isinstance(plaintext, dict):
            serialized_plaintext = json.dumps(
                    plaintext,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )

        else:
            serialized_plaintext = plaintext

        return self._fernet.encrypt(serialized_plaintext.encode()).decode()

    def decrypt(self, encrypted_text: str, to_json: bool = False) -> str | dict:
        """Decrypts an encrypted string back into its original string or dictionary.

        Because the Encryption class accepts both strings and dictionaries,
        dictionaries are serialized into JSON before encryption. As a result,
        decrypting them returns a raw JSON string by default which means a dictionary
        will return a string when decrypted instead of a dictionary. Set `to_json=True`
        to reconstruct and return the original dictionary.

        Args:
            encrypted_text (str): The encrypted string to be decrypted.
            to_json (bool, optional): If True, parses the decrypted string as
                JSON and returns a dictionary. Defaults to False.

        Returns:
            str | dict: The decrypted plaintext string, or a reconstructed
            dictionary if `to_json` is True.

        Raises:
            TypeError: If `to_json` is not a boolean.
            json.decoder.JSONDecodeError: If `to_json` is True, but the original
                decrypted data is not valid JSON (e.g., it was originally a plain string).

        Examples:
            Decrypting a standard string:
            >>> cipher = Encryption()
            >>> token = cipher.encrypt("secret message")
            >>> cipher.decrypt(token)
            'secret message'

            Decrypting a dictionary:
            >>> token = cipher.encrypt({"user_id": 42, "role": "admin"})
            >>> cipher.decrypt(token, to_json=True)
            {'user_id': 42, 'role': 'admin'}
        """
        self._validate(encrypted_text)

        if not isinstance(to_json, bool):
            raise TypeError(f"to_json must be a bool. Got type {type(to_json).__name__}")

        decrypted_str = self._fernet.decrypt(encrypted_text.encode()).decode()

        if to_json:
            return json.loads(decrypted_str)
        return decrypted_str










