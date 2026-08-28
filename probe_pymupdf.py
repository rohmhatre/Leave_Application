import sys
try:
    import fitz
    print('imported fitz, version', fitz.__doc__[:50])
except Exception as e:
    print('failed import fitz', e)

print('modules with mu', [m.name for m in __import__('pkgutil').iter_modules() if 'mu' in m.name.lower()])
