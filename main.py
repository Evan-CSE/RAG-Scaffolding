from utils.extractor import Extractor

extractor = Extractor("sample_pdf/sample.pdf")
text = extractor.extract()
extractor.save_raw_text("sample_pdf/sample.txt")
print(text)