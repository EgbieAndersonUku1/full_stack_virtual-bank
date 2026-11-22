from django.test import TestCase
from cryptography.fernet import InvalidToken

from utils.security.encryption import Encryption


class EncryptionTest(TestCase):
    """
    Tests the Encryption utility's key generation, encryption and decryption
    functionality, including input validation and invalid key or ciphertext
    handling.
    """

    def setUp(self) -> None:
        self.encryption_key = Encryption.generate_key()
        self.encryption     = Encryption(self.encryption_key)
        self.plaintext      = "All hail, Macbeth! hail to thee, thane of Glamis! path"

    def test_encryption_encrypts_plaintext(self):

        # GIVEN: A valid encryption key and plaintext.
        # WHEN: The plaintext is encrypted.
        ciphertext = self.encryption.encrypt(self.plaintext)
        self.assertNotEqual(ciphertext, self.plaintext, "plaintext should not be equal to the cipher text")

        # THEN: The method returns ciphertext different from the plaintext.
        self.assertIsInstance(ciphertext, str, "Expected the ciphertext to be a string")

    def test_encryption_key_generation(self):

        # GIVEN: The caller needs a new encryption key.
        # WHEN: A key is generated.
        encryption_key = Encryption.generate_key()

        # THEN: The key is a string and can initialise Encryption.
        self.assertIsInstance(encryption_key, str)

        encryption = Encryption(encryption_key)
        self.assertIsInstance(encryption, Encryption)

    def test_decryption_decrypts_ciphertext(self):

        # GIVEN: A valid encryption key and plaintext.
        ciphertext = self.encryption.encrypt(self.plaintext)

        # WHEN: A ciphertext is decrypted
        decrypted_text = self.encryption.decrypt(ciphertext)

        # THEN: The method returns a plaintext that is exactly the same that was encrypted
        self.assertEqual(decrypted_text, self.plaintext, "The decrypted text should equal the plaintext")

    def test_encryption_encrypts_empty_string(self):

        # GIVEN: A valid encryption key and an empty string.
        empty_string = ""

        # WHEN: The empty string is encrypted.
        encrypted_string = self.encryption.encrypt(empty_string)

        # THEN: The result is ciphertext.
        self.assertIsInstance(encrypted_string, str)
        self.assertNotEqual(encrypted_string, empty_string)

        # AND: The ciphertext can be decrypted back to an empty string.
        decrypted_string = self.encryption.decrypt(encrypted_string)
        self.assertEqual(decrypted_string, empty_string)

    def test_encryption_rejects_non_string_plaintext(self):

        # GIVEN: An integer is supplied instead of plaintext.
        invalid_plaintext = 12345

        # WHEN: The invalid plaintext is passed to encryption.
        # THEN: A TypeError is raised with the expected message.
        with self.assertRaisesRegex(
            TypeError,
            "Expected the value to be a string or dict. Got type int"
        ):
            self.encryption.encrypt(invalid_plaintext)

    def test_decryption_rejects_non_string_ciphertext(self):

        # GIVEN: An integer is supplied instead of ciphertext.
        invalid_ciphertext = 1245

        # WHEN: The invalid ciphertext is passed to decryption.
        # THEN: A TypeError should be raised with the expected message.
        with self.assertRaisesRegex(
            TypeError,
            "encrypted_text must be a str or bytes. Got type int"
        ):
            self.encryption.decrypt(invalid_ciphertext)

    def test_decryption_rejects_invalid_ciphertext(self):

        # GIVEN: An invalid ciphertext string.
        invalid_ciphertext = "1245"

        # WHEN: The invalid ciphertext is passed to decryption.
        # THEN: An InvalidToken exception should be raised.
        with self.assertRaises(InvalidToken):
            self.encryption.decrypt(invalid_ciphertext)

    def test_decryption_rejects_ciphertext_encrypted_with_different_key(self):

        # GIVEN: Plaintext is encrypted using the original encryption key.
        encrypted_text = self.encryption.encrypt(self.plaintext)

        # WHEN: A different encryption key is used to decrypt the ciphertext.
        different_encryption_key = Encryption.generate_key()
        different_encryption = Encryption(different_encryption_key)

        # THEN: An InvalidToken exception should be raised.
        with self.assertRaises(InvalidToken):
            different_encryption.decrypt(encrypted_text)

    def test_encryption_rejects_non_string_key(self):

        # GIVEN: An integer is supplied instead of an encryption key.
        invalid_encryption_key = 1234

        # WHEN: The invalid key is passed to the constructor.
        # THEN: A TypeError should be raised with the expected message.
        with self.assertRaisesRegex(
            TypeError,
            "The encryption key is not a string. Expected a string got int"
        ):
            Encryption(invalid_encryption_key)

    def test_encryption_rejects_invalid_fernet_key(self):

        # GIVEN: A string that does not conform to Fernet's key format.
        invalid_encryption_key = "not-a-valid-fernet-key"

        # WHEN: The invalid key is passed to the constructor.
        # THEN: A ValueError should be raised.
        with self.assertRaisesRegex(
            ValueError,
            "Fernet key must be 32 url-safe base64-encoded bytes."
        ):
            Encryption(invalid_encryption_key)

    def test_encryption_encrypts_dict(self):

        # GIVEN: A dictionary is pass in as a payload to the Encryption
        payload = {
            "from": "test_example.com",
            "to": "from@example.com",
            "subject": "test subject"
        }

         # WHEN: The encrypt method called
         # THEN: The result would be a ciphertext and a string.
        encrypted_payload = self.encryption.encrypt(payload)

        self.assertIsInstance(encrypted_payload, str)
        self.assertNotEqual(encrypted_payload, payload)

        # decrypt encrypted payload to see if matches payload
        decrypted_payload = self.encryption.decrypt(encrypted_payload, to_json=True)

        self.assertEqual(decrypted_payload,
                         payload,
                         "Decrypted payload should match plaintext payload")






