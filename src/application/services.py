from src.domain.interfaces import TextProcessor
from src.infrastructure.extraction.smart_extractor import ExtractorAdapter

class DocumentProcessingService:
    """Application service for orchestrating document processing."""
    
    def __init__(self, extractor: ExtractorAdapter, processor: TextProcessor):
        self.extractor = extractor
        self.processor = processor

    def process_and_normalize(self, raw_text_save_path: str = None) -> str:
        # 1. Extract raw text
        raw_text = self.extractor.extract()
        
        # 2. Save raw text if requested
        if raw_text_save_path:
            self.extractor.save_raw_text(raw_text, raw_text_save_path)
        
        # 3. Normalize
        normalized_text = self.processor.clean(raw_text)
        
        return normalized_text
