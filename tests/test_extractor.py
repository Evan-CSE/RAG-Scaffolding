import unittest
from unittest.mock import MagicMock, patch
from src.infrastructure.extraction.strategies import (
    PyPDFExtractionStrategy,
    OCRExtractionStrategy,
    EasyOCRExtractionStrategy
)
from src.infrastructure.extraction.smart_extractor import (
    SmartExtractor,
    ExtractorAdapter
)

class TestStrategies(unittest.TestCase):
    def test_pypdf_strategy(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted Text"
        strategy = PyPDFExtractionStrategy()
        result = strategy.extract_page(0, mock_page)
        self.assertEqual(result, "Extracted Text")

    @patch("src.infrastructure.extraction.strategies.Image")
    @patch("src.infrastructure.extraction.strategies.pytesseract")
    def test_ocr_strategy(self, mock_tesseract, mock_image):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.load_page.return_value = mock_page
        mock_page.get_pixmap.return_value = MagicMock(width=100, height=100, samples=b"000")
        mock_tesseract.image_to_string.return_value = "OCR Text"

        strategy = OCRExtractionStrategy(mock_doc)
        result = strategy.extract_page(0, None)
        self.assertEqual(result, "OCR Text")

class TestEasyOCRExtractionStrategy(unittest.TestCase):
    @patch("src.infrastructure.extraction.strategies.easyocr.Reader")
    def test_easyocr_strategy(self, mock_reader_cls):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.load_page.return_value = mock_page
        mock_page.get_pixmap.return_value = MagicMock()
        
        mock_reader = mock_reader_cls.return_value
        mock_reader.readtext.return_value = ["Bengali", "OCR", "Content"]
        mock_page.get_pixmap.return_value.tobytes.return_value = b"fake_png_data"

        strategy = EasyOCRExtractionStrategy(mock_doc)
        result = strategy.extract_page(0, None)
        
        self.assertEqual(result, "Bengali\nOCR\nContent")
        mock_reader.readtext.assert_called_once()

class TestSmartExtractor(unittest.TestCase):
    @patch("src.infrastructure.extraction.smart_extractor.PdfReader")
    def test_extract_all_success(self, mock_reader_cls):
        mock_reader = mock_reader_cls.return_value
        mock_reader.pages = [MagicMock(), MagicMock()]
        
        primary = MagicMock()
        primary.extract_page.return_value = "Page Content"
        
        extractor = SmartExtractor("dummy.pdf", primary)
        result = extractor.extract_all()
        
        self.assertIn("Page Content", result)
        self.assertEqual(primary.extract_page.call_count, 2)

    @patch("src.infrastructure.extraction.smart_extractor.PdfReader")
    def test_fallback_logic(self, mock_reader_cls):
        mock_reader = mock_reader_cls.return_value
        mock_reader.pages = [MagicMock()]
        
        primary = MagicMock()
        primary.extract_page.return_value = ""  # Trigger fallback
        
        fallback = MagicMock()
        fallback.extract_page.return_value = "Fallback Content"

        extractor = SmartExtractor("dummy.pdf", primary, fallback_strategy=fallback)
        result = extractor.extract_all()
        
        self.assertEqual(result, "Fallback Content")
        fallback.extract_page.assert_called_once()

class TestExtractorAdapter(unittest.TestCase):
    @patch("src.infrastructure.extraction.smart_extractor.fitz.open")
    @patch("src.infrastructure.extraction.smart_extractor.PdfReader")
    @patch("src.infrastructure.extraction.smart_extractor.SmartExtractor")
    def test_adapter_integration(self, mock_smart, mock_reader, mock_fitz):
        mock_smart_instance = mock_smart.return_value
        mock_smart_instance.extract_all.return_value = "Final Text"
        
        adapter = ExtractorAdapter("dummy.pdf")
        result = adapter.extract()
        
        self.assertEqual(result, "Final Text")
        mock_smart_instance.extract_all.assert_called_once()

if __name__ == "__main__":
    unittest.main()
