from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Any

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

class ExtractionStrategy(ABC):
    """Base interface for different page extraction methods."""
    @abstractmethod
    def extract_page(self, page_number: int, page_obj: Any) -> Optional[str]:
        """Extract text from a specific page object."""
        raise NotImplementedError
