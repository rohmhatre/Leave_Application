import sys
print('sys.executable', sys.executable)
try:
    import pymupdf
    print('imported pymupdf', pymupdf.__version__)
except Exception as e:
    print('failed importing pymupdf', e)
try:
    import fitz
    print('imported fitz', fitz.__version__)
except Exception as e:
    print('failed importing fitz', e)
