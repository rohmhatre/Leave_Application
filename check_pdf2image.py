try:
    import pdf2image
    print('pdf2image available')
except Exception as e:
    print('pdf2image not available', e)
