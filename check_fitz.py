try:
    import fitz
    print('PyMuPDF available')
except Exception as e:
    print('PyMuPDF not available', e)
