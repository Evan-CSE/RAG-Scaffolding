from utils.extractor import Extractor
from utils.normalizer import get_processor

# 1. Initialize Extractor (now strictly for reading)
extractor = Extractor("sample_pdf/sample.pdf")

# 2. Extract raw text
raw_text = extractor.extract()
extractor.save_raw_text("sample_pdf/sample.txt")

# 3. Initialize Normalizer/Processor
processor = get_processor()

# 4. Normalize the text
normalized_text = processor.clean(raw_text)

# 5. Output results
print("--- Normalized Text ---")
print(normalized_text)

# 6. Save normalized text
with open("sample_pdf/sample_normalized.txt", "w", encoding="utf-8") as f:
    f.write(normalized_text)

