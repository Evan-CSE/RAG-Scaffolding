import unicodedata
import re
from typing import List, Tuple, Optional
from src.domain.interfaces import TextProcessor

try:
    from bnunicodenormalizer import Normalizer as BNNormalizer
    HAS_BNUNICODE = True
except ImportError:
    HAS_BNUNICODE = False

class BanglaTextProcessor(TextProcessor):
    """
    Standalone Bangla Unicode normalization and validation for RAG pipelines.
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
        if not text:
            return ""
        
        if self._engine:
            return self._engine.normalize(text)
        
        return self._manual_normalize(text)
    
    def validate(self, text: str) -> List[Tuple[int, str, str]]:
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
        text = unicodedata.normalize("NFC", text)
        text = text.replace("\u200c", "")
        text = re.sub(
            r'[0-9]', 
            lambda m: chr(ord(m.group()) + 0x09E6 - ord('0')), 
            text
        )
        return text.strip()

_default_processor = None

def get_processor(config: dict = None) -> BanglaTextProcessor:
    global _default_processor
    if _default_processor is None or config:
        _default_processor = BanglaTextProcessor(config)
    return _default_processor
