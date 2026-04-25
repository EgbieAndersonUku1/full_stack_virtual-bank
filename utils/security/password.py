import re

class PasswordStrengthChecker:
    """
    A class to check the strength of a password based on various criteria.

    Attributes:
        password (str): The password to be checked.
        default_length (int): The minimum length required for the password.
    """

    def __init__(self, password, default_length=8) -> None:
        """
        Initializes the PasswordStrengthChecker with a password and a default minimum length.

        Args:
            password (str): The password to be checked.
            default_length (int, optional): The minimum length required for the password. Defaults to 8.
        """
        self.password = password
        self.default_length = default_length

    def set_password(self, password: str) -> None:
        """
        Sets a new password.

        Args:
            password (str): The new password to be checked.
        """
        self.password = password

    def set_password_length(self, password_length: int) -> None:
        """
        Sets a new minimum length requirement for the password.

        Args:
            password_length (int): The new minimum length for the password.
        """
        self.default_length = password_length

    def contains_at_least_length_chars(self) -> bool:
        """
        Checks if the password contains at least the minimum required number of characters.
        """
        return len(self.password) >= self.default_length

    def contains_at_least_one_number(self) -> bool:
        """Checks if the password contains at least one numeric digit."""
        return bool(re.search(r'\d', self.password))

    def contains_lowercases(self) -> bool:
        """Checks if the password contains at least one lowercase letter."""
        return bool(re.search(r'[a-z]', self.password))

    def contains_uppercases(self) -> bool:
        """Checks if the password contains at least one uppercase letter."""
        return bool(re.search(r'[A-Z]', self.password))

    def contains_special_chars(self) -> bool:
        """Checks if the password contains at least one special character."""
        return bool(re.search(r'[\W_]', self.password))

    def is_strong_password(self) -> bool:
        """
        Evaluates whether the password is strong based on all criteria.
        """
        return (
            self.contains_at_least_length_chars()
            and self.contains_at_least_one_number()
            and self.contains_lowercases()
            and self.contains_uppercases()
            and self.contains_special_chars()
        )