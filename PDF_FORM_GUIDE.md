# PDF Form Integration Guide

## Overview
This guide shows how to integrate your existing PDF form (WA0002) with the Leave Application system.

---

## Setup Steps

### 1. Place Your PDF Template
- Place your PDF form file in: `static/forms/WA0002.pdf`
- Directory structure:
  ```
  Leave_Application/
  ├── static/
  │   └── forms/
  │       └── WA0002.pdf  ← Your PDF template here
  ├── core/
  ├── manage.py
  └── ...
  ```

### 2. Extract Form Field Names
Run this command to identify all form fields in your PDF:

```bash
python extract_pdf_fields.py static/forms/WA0002.pdf
```

**Output example:**
```
✅ Found 8 form fields:

Field Name: StudentName
  Type: /Tx (Text)
  Value: N/A

Field Name: RollNumber
  Type: /Tx (Text)
  Value: N/A

Field Name: LeaveFromDate
  Type: /Tx (Text)
  Value: N/A

...
```

### 3. Map Fields in Django View
If your PDF contains AcroForm fields, update the `data` dictionary in `core/views.py` within `download_application_pdf()` as shown below and the code will fill them automatically:

```python
data = {
    'StudentName': leave.student.get_full_name(),
    'RollNumber': leave.student.roll_number,
    'LeaveFromDate': str(leave.from_date),  # Adjust to your actual field name
    'LeaveToDate': str(leave.to_date),
    'LeaveDays': str((leave.to_date - leave.from_date).days + 1),
    'Purpose': leave.purpose,
    # Add all your PDF form fields here
}
```

If the template **does not** have form fields (e.g. a scanned/static PDF), the view now falls back to drawing the data at fixed coordinates. In that case, look in `download_application_pdf()` for a `coords` dictionary defined like this:

```python
coords = {
    'name': (150, 710),            # after "Name of the student:"
    'roll': (440, 710),            # on same line, near right blank
    'academic_unit': (150, 690),   # next line down
    # …more entries for each field…
}
```

Adjust the `(x, y)` values until the text lines up with the blank spaces on your form. Many PDF viewers (Adobe Acrobat, PDF‑XChange, etc.) display the cursor position or provide a ruler; use that to read off coordinates. Remember the origin (0,0) is bottom-left, so you may need to subtract from the page height (612×792 points) when measuring. Coordinates are in points (72 points = 1 inch).

Both approaches coexist; the view chooses the appropriate one automatically based on whether any form fields were detected.

**Match the keys to your extracted field names exactly when using AcroForms!**

---

## PDF Field Types

| Type Code | Field Type | Example |
|-----------|-----------|---------|
| `/Tx` | Text Input | Name, Email, Purpose |
| `/Ch` | Choice (Dropdown) | Status, Programme |
| `/Btn` | Button/Checkbox | Approve, Reject |
| `/Sig` | Signature | (Non-fillable) |

---

## Important Notes

### Requirements
```bash
pip install PyPDF2
```

### PDF Support
- ✅ **Supported**: AcroForm PDFs (form fields with proper naming)
- ❌ **NOT Supported**: Scan images without form fields (you'll need OCR)
- ⚠️ **Partial**: Some encrypted PDFs may not work

### Fallback Behavior
If your PDF template is missing or cannot be processed:
- The system automatically generates a formatted PDF on-the-fly
- All student data is still included
- Users can still download and print

---

## Troubleshooting

### "No form fields found in this PDF"
- Your PDF may not be a proper fillable form
- Try opening it in Adobe Reader to verify form fields exist
- If unsure, create a new form using Adobe Form Creator or similar tools

### "Error reading PDF"
- Ensure the PDF is not corrupted
- Check file permissions
- Try opening in a PDF reader first

### Fields not being filled
- Verify field names match exactly (case-sensitive)
- Check data types (numbers, dates, etc.)
- Some PDFs may have hidden fields

---

## Advanced: Custom Python Script

If you need more control, use the extract_pdf_fields utility:

```python
from PyPDF2 import PdfReader, PdfWriter

# Read template
reader = PdfReader('static/forms/WA0002.pdf')
writer = PdfWriter()

# Copy pages
for page in reader.pages:
    writer.add_page(page)

# Update fields
data = {
    'StudentName': 'John Doe',
    'RollNumber': '25m0001',
    # ... more fields
}

for field, value in data.items():
    try:
        writer.update_page_form_field_value(writer.pages[0], field, str(value))
    except:
        print(f"Could not fill field: {field}")

# Save
with open('output.pdf', 'wb') as f:
    writer.write(f)
```

---

## Example Workflow

1. **Admin receives** WA0002.pdf template from department
2. **Admin runs**: `python extract_pdf_fields.py static/forms/WA0002.pdf`
3. **Admin updates** field mapping in `download_application_pdf()` function
4. **Student downloads** PDF → Form auto-fills with their data
5. **Student prints** and submits (or signs electronically)

---

## Testing

After setup, test the feature:

1. Create a student account
2. Apply for leave
3. View application
4. Click **"Download as PDF"**
5. Verify all fields are correctly filled

---

## Support

If PDF doesn't fill correctly:
- Check `extract_pdf_fields.py` output
- Verify student data exists
- Check Django console for errors
- Try fallback auto-generated PDF

For custom requirements, extend the view with PDF library of choice (pypdf, reportlab, pdfrw, etc.)
