import unittest
from scraper import sanitize_for_sheets

class TestScraperSanitization(unittest.TestCase):
    def test_sanitize_for_sheets_dangerous_characters(self):
        # Test dangerous characters are prepended with a single quote
        self.assertEqual(sanitize_for_sheets("=SUM(A1:B1)"), "'=SUM(A1:B1)")
        self.assertEqual(sanitize_for_sheets("+1+1"), "'+1+1")
        self.assertEqual(sanitize_for_sheets("-1"), "'-1")
        self.assertEqual(sanitize_for_sheets("@foo"), "'@foo")

    def test_sanitize_for_sheets_safe_strings(self):
        # Test safe strings are returned unchanged
        self.assertEqual(sanitize_for_sheets("Hello World"), "Hello World")
        self.assertEqual(sanitize_for_sheets("123"), "123")
        self.assertEqual(sanitize_for_sheets(""), "")

    def test_sanitize_for_sheets_non_strings(self):
        # Test non-string values are returned unchanged
        self.assertEqual(sanitize_for_sheets(123), 123)
        self.assertEqual(sanitize_for_sheets(-123), -123)
        self.assertIsNone(sanitize_for_sheets(None))

if __name__ == '__main__':
    unittest.main()
