import unicodedata
import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

try:
    from bnunicodenormalizer import Normalizer as BNNormalizer
    HAS_BNUNICODE = True
except ImportError:
    HAS_BNUNICODE = False


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


class BanglaTextProcessor(TextProcessor):
    """
    Standalone Bangla Unicode normalization and validation for RAG pipelines.
    Works with ANY text source, not just PDFs.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.use_bn_unicode = self.config.get("use_bn_unicode", True)
        
        if HAS_BNUNICODE and self.use_bn_unicode:
            self._engine = BNNormalizer(
                allow_english=True,
                normalize_bengali_digits=True,
            )
        else:
            self._engine = None
    
    def clean(self, text: str) -> str:
        """Main entry point - normalize Bangla text for RAG."""
        if not text:
            return ""
        
        # Use bnunicodenormalizer if available
        if self._engine:
            return self._engine.normalize(text)
        
        # Fallback to manual implementation
        return self._manual_normalize(text)
    
    def validate(self, text: str) -> List[Tuple[int, str, str]]:
        """Identify issues in the provided text (Unicode issues, control chars, etc)."""
        if not text:
            return []
        issues = []
        for idx, char in enumerate(text):
            if unicodedata.normalize("NFC", char) != char:
                issues.append((idx, char, "non-NFC"))
            if ord(char) < 32 and char not in ("\n", "\t", "\r"):
                issues.append((idx, char, "control-char"))
            if char in ("\u200c", "\u200d"):
                issues.append((idx, char, "zwj-zwnj"))
        return issues

    def _manual_normalize(self, text: str) -> str:
        """Manual NFC + ZWNJ + digit normalization."""
        text = unicodedata.normalize("NFC", text)
        text = text.replace("\u200c", "")
        text = re.sub(
            r'[0-9]', 
            lambda m: chr(ord(m.group()) + 0x09E6 - ord('0')), 
            text
        )
        
        return text.strip()


# Global instance for reuse across pipeline
_default_processor = None

def get_processor(config: dict = None) -> BanglaTextProcessor:
    """Factory - reuse processor instance across pipeline."""
    global _default_processor
    if _default_processor is None or config:
        _default_processor = BanglaTextProcessor(config)
    return _default_processor
