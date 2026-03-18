from src.infrastructure.extraction.smart_extractor import ExtractorAdapter
from src.infrastructure.normalization.bangla_processor import get_processor
from src.application.services import DocumentProcessingService

# 1. Initialize Infrastructure Adapters
extractor = ExtractorAdapter("sample_pdf/sample.pdf")
processor = get_processor()

# 2. Initialize Application Service (Depend on Abstractions)
service = DocumentProcessingService(extractor, processor)

# 3. Process and Normalize
normalized_text = service.process_and_normalize(raw_text_save_path="sample_pdf/sample.txt")

# 4. Output results
print("--- Normalized Text ---")
print(normalized_text)

# 5. Save normalized text
with open("sample_pdf/sample_normalized.txt", "w", encoding="utf-8") as f:
    f.write(normalized_text)

