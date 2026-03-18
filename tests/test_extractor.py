import unittest
from unittest.mock import MagicMock, patch
from utils.extractor import (
    BengaliTextProcessor,
    PyPDFExtractionStrategy,
    OCRExtractionStrategy,
    SmartExtractor,
    Extractor
)

class TestBengaliTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = BengaliTextProcessor()

    def test_clean_norm(self):
        # Result of normalization should be NFC
        text = "আম"  # Simplified example
        cleaned = self.processor.clean(text)
        self.assertEqual(cleaned, text)

    def test_clean_removes_zwj_zwnj(self):
        text = "TEST\u200c\u200d"
        cleaned = self.processor.clean(text)
        self.assertEqual(cleaned, "TEST")

    def test_validate_detects_issues(self):
        # Control char
        text = "Hello\x01World"
        issues = self.processor.validate(text)
        self.assertTrue(any(issue[2] == "control-char" for issue in issues))

        # ZWJ/ZWNJ
        text = "\u200c"
        issues = self.processor.validate(text)
        self.assertTrue(any(issue[2] == "zwj-zwnj" for issue in issues))

class TestStrategies(unittest.TestCase):
    def test_pypdf_strategy(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted Text"
        strategy = PyPDFExtractionStrategy()
        result = strategy.extract_page(0, mock_page)
        self.assertEqual(result, "Extracted Text")

    @patch("utils.extractor.Image")
    @patch("utils.extractor.pytesseract")
    def test_ocr_strategy(self, mock_tesseract, mock_image):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.load_page.return_value = mock_page
        mock_page.get_pixmap.return_value = MagicMock(width=100, height=100, samples=b"000")
        mock_tesseract.image_to_string.return_value = "OCR Text"

        strategy = OCRExtractionStrategy(mock_doc)
        result = strategy.extract_page(0, None)
        self.assertEqual(result, "OCR Text")

class TestSmartExtractor(unittest.TestCase):
    @patch("utils.extractor.PdfReader")
    def test_extract_all_success(self, mock_reader_cls):
        mock_reader = mock_reader_cls.return_value
        mock_reader.pages = [MagicMock(), MagicMock()]
        
        primary = MagicMock()
        primary.extract_page.return_value = "Page Content"
        
        processor = MagicMock()
        processor.clean.side_effect = lambda x: x
        processor.validate.return_value = []

        extractor = SmartExtractor("dummy.pdf", primary, processor=processor)
        result = extractor.extract_all()
        
        self.assertIn("Page Content", result)
        self.assertEqual(primary.extract_page.call_count, 2)

    @patch("utils.extractor.PdfReader")
    def test_fallback_logic(self, mock_reader_cls):
        mock_reader = mock_reader_cls.return_value
        mock_reader.pages = [MagicMock()]
        
        primary = MagicMock()
        primary.extract_page.return_value = None  # Trigger fallback
        
        fallback = MagicMock()
        fallback.extract_page.return_value = "Fallback Content"

        extractor = SmartExtractor("dummy.pdf", primary, fallback_strategy=fallback)
        result = extractor.extract_all()
        
        self.assertEqual(result, "Fallback Content")
        fallback.extract_page.assert_called_once()

class TestExtractorFacade(unittest.TestCase):
    @patch("utils.extractor.fitz.open")
    @patch("utils.extractor.PdfReader")
    @patch("utils.extractor.SmartExtractor")
    def test_facade_integration(self, mock_smart, mock_reader, mock_fitz):
        mock_smart_instance = mock_smart.return_value
        mock_smart_instance.extract_all.return_value = "Final Text"
        
        facade = Extractor("dummy.pdf")
        result = facade.extract()
        
        self.assertEqual(result, "Final Text")
        mock_smart_instance.extract_all.assert_called_once()

if __name__ == "__main__":
    unittest.main()
