import unittest
from src.infrastructure.normalization.bangla_processor import BanglaTextProcessor

class TestBanglaTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = BanglaTextProcessor(config={"use_bn_unicode": False})

    def test_clean_norm(self):
        text = "\u0995\u09cd\u09b0\u09bf."
        cleaned = self.processor.clean(text)
        import unicodedata
        self.assertEqual(cleaned, unicodedata.normalize("NFC", text))

    def test_clean_removes_zwnj(self):
        # User updated logic to only remove ZWNJ (\u200c)
        text = "TEST\u200c\u200d"
        cleaned = self.processor.clean(text)
        self.assertEqual(cleaned, "TEST\u200d")

    def test_digit_normalization(self):
        text = "123"
        cleaned = self.processor.clean(text)
        self.assertEqual(cleaned, "১২৩")

    def test_validate_detects_issues(self):
        text = "Hello\x01World"
        issues = self.processor.validate(text)
        self.assertTrue(any(issue[2] == "control-char" for issue in issues))
        
        text = "\u200c"
        issues = self.processor.validate(text)
        self.assertTrue(any(issue[2] == "zwj-zwnj" for issue in issues))

if __name__ == "__main__":
    unittest.main()
