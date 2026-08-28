from PyPDF2 import PdfReader
reader = PdfReader('Official_acad_leave_2901014.pdf')
page = reader.pages[0]
print('mediaBox', page.mediabox)
print('width x height', float(page.mediabox.width), float(page.mediabox.height))