from PyPDF2 import PdfReader

reader = PdfReader('test_pdf.pdf')
page = reader.pages[0]
text = page.extract_text()
print('---- extracted text ----')
print(text)