from typing import List, Optional, Any
from PyPDF2 import PdfReader
import fitz
from src.domain.interfaces import ExtractionStrategy, TextProcessor
from src.infrastructure.extraction.strategies import PyPDFExtractionStrategy, EasyOCRExtractionStrategy

class SmartExtractor:
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
            self.results.append(text)
        return "\n\n".join(self.results)

    def _extract_with_fallback(self, page_number: int, page_obj: Any) -> str:
        text = self.primary_strategy.extract_page(page_number, page_obj)
        should_fallback = text is None or text.strip() == "" or self._is_garbled(text)
        
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
        if not text:
            return False
        cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len([c for c in text if c.isalpha()])
        if total_chars > 0 and cjk_count / total_chars > 0.3:
            return True
        if '(cid:' in text.lower():
            return True
        return False

class ExtractorAdapter:
    """Adapter for extracting text using SmartExtractor."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = fitz.open(file_path)
        self._engine = SmartExtractor(
            file_path=file_path,
            primary_strategy=PyPDFExtractionStrategy(),
            fallback_strategy=EasyOCRExtractionStrategy(self.doc, "ben"),
            processor=None
        )

    def extract(self) -> str:
        return self._engine.extract_all()

    def save_raw_text(self, text: str, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
