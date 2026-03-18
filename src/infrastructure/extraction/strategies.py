import platform
from typing import Any, Optional
import fitz
import pytesseract
import easyocr
from PIL import Image
from src.domain.interfaces import ExtractionStrategy

class PyPDFExtractionStrategy(ExtractionStrategy):
    """Direct text extraction using PyPDF2."""
    def extract_page(self, page_number: int, page_obj: Any) -> Optional[str]:
        return getattr(page_obj, "extract_text")() if hasattr(page_obj, "extract_text") else None

class OCRExtractionStrategy(ExtractionStrategy):
    """OCR-based extraction using fitz and pytesseract."""
    def __init__(self, doc: "fitz.Document", lang: str = "ben"):
        self.doc = doc
        self.lang = lang
        if platform.system() == "Windows":
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def extract_page(self, page_number: int, page_obj: Any = None) -> str:
        page = self.doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return str(pytesseract.image_to_string(img, lang=self.lang))

class EasyOCRExtractionStrategy(ExtractionStrategy):
    def __init__(self, doc: "fitz.Document", lang: str = "ben"):
        self.doc = doc
        self.lang = lang
        self.reader = easyocr.Reader(['bn', 'en'])
    
    def extract_page(self, page_number: int, page_obj: Any = None) -> str:
        page = self.doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        result = self.reader.readtext(img_bytes, detail=0)
        return "\n".join(result)
