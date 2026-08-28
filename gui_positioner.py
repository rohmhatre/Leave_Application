"""Simple GUI to position text overlays on a PDF page.

Usage: run this script from the project root. It opens the first page of
`test_pdf.pdf` (or any file you supply) and displays it in a window.  Choose a field key from the dropdown or click "Confirm choice" to set it,
then click on the image to position that field.  (Do **not** type the actual
student value; enter the logical key such as `name`, `roll`, `programme`, etc.)  Red crosses and labels show the current
coordinates for all fields.  When you're done press "Print coords" to dump the
final dictionary to the console (copy/paste back into `core/views.py`).

Coordinates are stored in PDF points with origin at bottom-left (the same
units that ReportLab uses). The canvas uses a top-left origin; the script
performs the necessary conversion automatically.
"""

import fitz
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

# default PDF to load; you can edit this or pass another file path below
PDF_FILE = 'test_pdf.pdf'
PAGE = 0

# list of logical field keys used in views.py
FIELD_KEYS = [
    'name','roll','academic_unit','programme','discipline',
    'specialization','from_date','to_date','days','purpose'
]

# load document
try:
    doc = fitz.open(PDF_FILE)
except Exception as e:
    raise RuntimeError(f"could not open PDF {PDF_FILE}: {e}")
page = doc.load_page(PAGE)
page_width, page_height = page.rect.width, page.rect.height
# render at 72dpi so pixel == point
pix = page.get_pixmap(dpi=72)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

coords = {}
selected_field_var = tk.StringVar(value='')
selected_field = None

root = tk.Tk()
root.title('PDF Text Positioner')

canvas = tk.Canvas(root, width=pix.width, height=pix.height)
canvas_img = ImageTk.PhotoImage(img)
canvas.create_image(0, 0, anchor='nw', image=canvas_img)
canvas.grid(row=0, column=0, columnspan=3)

label = tk.Label(root, text='No field selected')
label.grid(row=1, column=0, columnspan=2, sticky='w')

# dropdown for choosing field key
field_menu = tk.OptionMenu(root, selected_field_var, *FIELD_KEYS)
field_menu.grid(row=1, column=2, sticky='e')

# add small instruction
instr = tk.Label(root, text='pick key before clicking')
instr.grid(row=2, column=0, columnspan=3, sticky='w')


def redraw():
    canvas.delete('marker')
    for k, (x, y) in coords.items():
        # convert PDF coordinate (origin bottom-left) to canvas coordinate
        cy = page_height - y
        canvas.create_line(x-3, cy, x+3, cy, fill='red', tags='marker')
        canvas.create_line(x, cy-3, x, cy+3, fill='red', tags='marker')
        canvas.create_text(x+5, cy+5, text=k, anchor='nw', fill='red', tags='marker')


def on_click(event):
    global selected_field
    if not selected_field:
        messagebox.showinfo('Select field', 'Please choose a field name first')
        return
    # convert back to PDF coordinates
    x = event.x
    y = page_height - event.y
    coords[selected_field] = (x, y)
    label.config(text=f"Placed '{selected_field}' at {(x, y)}")
    redraw()


def choose_field():
    global selected_field
    # read from dropdown
    name = selected_field_var.get()
    if name:
        selected_field = name
        label.config(text=f"Selected '{selected_field}'; click on image")


def print_coords():
    print('coords = {')
    for k, (x, y) in coords.items():
        print(f"    '{k}': ({x:.1f}, {y:.1f}),")
    print('}')
    messagebox.showinfo('Coords printed', 'Coordinates written to console.')


def save_coords():
    path = filedialog.asksaveasfilename(defaultextension='.py',
                                        filetypes=[('Python','*.py')])
    if path:
        with open(path, 'w') as f:
            f.write('coords = ' + repr(coords) + '\n')
        messagebox.showinfo('Saved', f'Coordinates saved to {path}')


canvas.bind('<Button-1>', on_click)

btn1 = tk.Button(root, text='Confirm choice', command=choose_field)
btn1.grid(row=3, column=0, sticky='w')
btn2 = tk.Button(root, text='Print coords', command=print_coords)
btn2.grid(row=3, column=1)
btn3 = tk.Button(root, text='Save coords', command=save_coords)
btn3.grid(row=3, column=2)

root.mainloop()
