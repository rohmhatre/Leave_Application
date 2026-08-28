#!/usr/bin/env python
"""
Utility script to extract form field names from a PDF file.
Use this to identify which fields exist in your WA0002.pdf
"""

import sys
from PyPDF2 import PdfReader

def extract_pdf_fields(pdf_path):
    """Extract and display all form field names from a PDF."""
    try:
        reader = PdfReader(pdf_path)
        
        if reader.is_encrypted:
            reader.decrypt('')
        
        fields = reader.get_fields()
        
        if not fields:
            print("❌ No form fields found in this PDF!")
            return False
        
        print(f"\n✅ Found {len(fields)} form fields:\n")
        print("-" * 60)
        
        for field_name, field_info in fields.items():
            field_type = field_info.get('/FT', 'Unknown')
            print(f"Field Name: {field_name}")
            print(f"  Type: {field_type}")
            print(f"  Value: {field_info.get('/V', 'N/A')}")
            print()
        
        print("-" * 60)
        print("\n📝 Copy the field names above into the 'data' dictionary in views.py")
        print("   Example mapping:")
        print("   data = {")
        for field_name in list(fields.keys())[:3]:
            print(f"       '{field_name}': 'value_here',")
        print("       ...")
        print("   }")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading PDF: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_fields.py <path_to_pdf>")
        print("Example: python extract_pdf_fields.py static/forms/WA0002.pdf")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    extract_pdf_fields(pdf_file)
