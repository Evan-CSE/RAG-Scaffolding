import unicodedata
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Tuple

import fitz
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
import platform
import easyocr

"""
This module provides a modular system for extracting text from PDF files, 
with a primary focus on Bengali language support and OCR fallback.
"""

class TextProcessor(ABC):
    """Abstract base for text processing and validation."""
    @abstractmethod
    def clean(self, text: str) -> str:
        """Clean and normalize the provided text."""
        raise NotImplementedError

    @abstractmethod
    def validate(self, text: str) -> List[Tuple[int, str, str]]:
        """Identify issues in the provided text."""
        raise NotImplementedError

class BengaliTextProcessor(TextProcessor):
    """Specific processor for Bengali text handling unicode normalization and ZWJ/ZWNJ."""
    
    def clean(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFC", text)
        return text.replace("\u200c", "").replace("\u200d", "")

    def validate(self, text: str) -> List[Tuple[int, str, str]]:
        if not text:
            return []
        issues = []
        for idx, char in enumerate(text):
            if unicodedata.normalize("NFC", char) != char:
                issues.append((idx, char, "non-NFC"))
            if ord(char) < 32 and char not in ("\n", "\t"):
                issues.append((idx, char, "control-char"))
            if char in ("\u200c", "\u200d"):
                issues.append((idx, char, "zwj-zwnj"))
        return issues

class ExtractionStrategy(ABC):
    """Base interface for different page extraction methods."""
    @abstractmethod
    def extract_page(self, page_number: int, page_obj: Any) -> Optional[str]:
        """Extract text from a specific page object."""
        raise NotImplementedError

class PyPDFExtractionStrategy(ExtractionStrategy):
    """Direct text extraction using PyPDF2."""
    def extract_page(self, page_number: int, page_obj: Any) -> Optional[str]:
        # Using Any for page_obj to accommodate different PDF library types
        return getattr(page_obj, "extract_text")() if hasattr(page_obj, "extract_text") else None

class OCRExtractionStrategy(ExtractionStrategy):
    """OCR-based extraction using fitz and pytesseract."""
    def __init__(self, doc: "fitz.Document", lang: str = "ben"):
        self.doc = doc
        self.lang = lang
        # ---- Minimal Windows fix. Will revert this ----
        if platform.system() == "Windows":
            # Replace this path with your actual Tesseract installation path
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
        self.reader = easyocr.Reader(['bn', 'en'])  # Bengali + English
    
    def extract_page(self, page_number: int, page_obj: Any = None) -> str:
        page = self.doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        
        # Save temporarily or convert to numpy
        img_bytes = pix.tobytes("png")
        result = self.reader.readtext(img_bytes, detail=0)
        return "\n".join(result)

class SmartExtractor:
    """Orchestrates extraction using multiple strategies and processors."""
    
    def __init__(
        self, 
        file_path: str,
        primary_strategy: ExtractionStrategy,
        fallback_strategy: Optional[ExtractionStrategy] = None,
        processor: Optional[TextProcessor] = None
    ):
        self.file_path = file_path
        self._reader = PdfReader(file_path)
        self.pages = self._reader.pages
        self.primary_strategy = primary_strategy
        self.fallback_strategy = fallback_strategy
        self.processor = processor
        self.results: List[str] = []

    def extract_all(self) -> str:
        self.results = []
        for i, page in enumerate(self.pages):
            print(f"[SmartExtractor] Processing page {i + 1}/{len(self.pages)}...")
            text = self._extract_with_fallback(i, page)
            
            # Narrowing Optional[TextProcessor]
            proc = self.processor
            if proc:
                text = proc.clean(text)
            
            self.results.append(text)
        
        return "\n\n".join(self.results)

    def _extract_with_fallback(self, page_number: int, page_obj: Any) -> str:
        text = self.primary_strategy.extract_page(page_number, page_obj)
        
        should_fallback = text is None or self._is_garbled(text)
        
        # Narrowing processor for validation
        proc = self.processor
        if not should_fallback and proc and text is not None:
            issues = proc.validate(text)
            if issues:
                print(f"[Warning] Found {len(issues)} unicode issues on page {page_number + 1}.")
                should_fallback = True
        
        fb_strat = self.fallback_strategy
        if should_fallback and fb_strat:
            print(f"[Info] Falling back to OCR for page {page_number + 1}...")
            text = fb_strat.extract_page(page_number, page_obj)
            
        return text if text is not None else ""

    def _is_garbled(self, text: str) -> bool:
        """Detect if text contains mojibake indicators."""
        if not text:
            return False
        
        # Check for high ratio of CJK characters (common mojibake indicator)
        # or control characters in Bengali context
        
        cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')  # CJK range
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars > 0 and cjk_count / total_chars > 0.3:
            return True  # >30% CJK chars in supposed Bengali text = garbled
        
        # Check for CID markers
        if '(cid:' in text.lower():
            return True
            
        return False

class Extractor:
    """
    Facade class for backward compatibility. 
    Maintains the original API while using the new modular engine.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = fitz.open(file_path)
        self.processor = BengaliTextProcessor()
        
        # Configure internal engine
        self._engine = SmartExtractor(
            file_path=file_path,
            primary_strategy=PyPDFExtractionStrategy(),
            fallback_strategy=EasyOCRExtractionStrategy(self.doc, "ben"),
            processor=self.processor
        )
        self.text = ""

    def extract(self) -> str:
        self.text = self._engine.extract_all()
        return self.text

    def save_raw_text(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.text)
