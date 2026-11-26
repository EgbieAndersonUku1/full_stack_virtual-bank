from unittest import TestCase

from utils.configuration import parse_old_fernet_keys


class ParseOldFernetKeysTests(TestCase):

    def test_returns_empty_list_when_no_keys_configured(self):
        result = parse_old_fernet_keys("")

        self.assertEqual(result, [])

    def test_returns_list_containing_single_key(self):
        result = parse_old_fernet_keys("key1")
        self.assertEqual(result, ["key1"])

    def test_returns_list_containing_multiple_keys(self):
        result = parse_old_fernet_keys("key1,key2,key3")
        self.assertEqual(result, ["key1", "key2", "key3"])

    def test_strips_whitespace_from_individual_keys(self):
        result = parse_old_fernet_keys(" key1 , key2 , key3 ")

        self.assertEqual(result, ["key1", "key2", "key3"])

    def test_preserves_malformed_empty_entries(self):
        result = parse_old_fernet_keys("key1,,key3")

        self.assertEqual(result, ["key1", "", "key3"])

    def test_preserves_empty_entry_after_trailing_comma(self):
        result = parse_old_fernet_keys("key1,key2,")

        self.assertEqual(result, ["key1", "key2", ""])

    def test_preserves_whitespace_only_entry_as_empty_string(self):
        result = parse_old_fernet_keys("   ")

        self.assertEqual(result, [""])
