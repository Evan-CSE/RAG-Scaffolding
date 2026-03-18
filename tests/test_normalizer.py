import unittest
from utils.normalizer import BanglaTextProcessor

class TestBanglaTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = BanglaTextProcessor(config={"use_bn_unicode": False}) # Test manual path

    def test_clean_norm(self):
        # NFC normalization
        text = "\u0995\u09cd\u09b0\u09bf." # ক্ র ি .
        cleaned = self.processor.clean(text)
        # Should be normalized NFC
        import unicodedata
        self.assertEqual(cleaned, unicodedata.normalize("NFC", text))

    def test_clean_removes_zwj_zwnj(self):
        text = "TEST\u200c\u200d"
        cleaned = self.processor.clean(text)
        self.assertEqual(cleaned, "TEST")

    def test_digit_normalization(self):
        text = "123"
        cleaned = self.processor.clean(text)
        self.assertEqual(cleaned, "১২৩")

    def test_ocr_artifact_fix(self):
        text = "ত্রি. নং শ্লী"
        cleaned = self.processor.clean(text)
        self.assertEqual(cleaned, "খ্রি. নং শ্রী")

    def test_validate_detects_issues(self):
        # Control char
        text = "Hello\x01World"
        issues = self.processor.validate(text)
        self.assertTrue(any(issue[2] == "control-char" for issue in issues))

        # ZWJ/ZWNJ
        text = "\u200c"
        issues = self.processor.validate(text)
        self.assertTrue(any(issue[2] == "zwj-zwnj" for issue in issues))

if __name__ == "__main__":
    unittest.main()
