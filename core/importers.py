"""Shared CSV import logic for student records.

Used by the admin upload view and the ``import_students`` management command
so that both accept the same file format and apply the same rules.
"""

import csv
from dataclasses import dataclass, field
from io import TextIOWrapper

from django.db import transaction

from .models import Student


@dataclass
class ImportResult:
    """What a single import did, for the caller to report however it likes."""

    created: int = 0
    updated: int = 0
    skipped_lines: list = field(default_factory=list)


def import_students_from_csv(stream):
    """Create or update Student rows from a CSV ``stream`` opened in binary.

    Recognised headers: roll_number, name, academic_unit, academic_programme,
    discipline, specialization.  Rows without a roll number are ignored, and
    rows carrying cells past the last header are skipped with their line
    numbers collected in the result.

    New students get their roll number as the initial password.  Existing ones
    keep their password and any field the CSV leaves blank.  The whole import
    runs in one transaction, so an error rolls all of it back.
    """
    # utf-8-sig strips the BOM that spreadsheet exports often add
    reader = csv.DictReader(
        TextIOWrapper(stream, encoding='utf-8-sig', newline=''),
        restkey='_extra',
    )
    result = ImportResult()

    with transaction.atomic():
        for row in reader:
            # cells beyond the last header collect under '_extra'; any
            # row with them has the wrong shape (usually an unquoted
            # comma), so skip it rather than import shifted columns
            extra = row.pop('_extra', None)
            if extra is not None:
                result.skipped_lines.append(reader.line_num)
                continue
            row = {(k or '').strip(): (v or '').strip() for k, v in row.items()}
            roll = row.get('roll_number', '')
            if not roll:
                continue

            name = row.get('name') or ''
            academic_unit = row.get('academic_unit', '')
            academic_programme = row.get('academic_programme', '')
            discipline = row.get('discipline', '')
            specialization = row.get('specialization', '')

            first_name = ''
            last_name = ''
            parts = str(name).split()
            if parts:
                first_name = parts[0]
                if len(parts) > 1:
                    last_name = ' '.join(parts[1:])

            student, created = Student.objects.get_or_create(
                roll_number=roll,
                defaults={'username': roll}
            )
            if created:
                student.first_name = first_name
                student.last_name = last_name
                student.set_password(roll)
                result.created += 1
            else:
                # ensure username is set for existing students
                if not student.username:
                    student.username = roll
                result.updated += 1

            # update these fields regardless
            student.first_name = first_name or student.first_name
            student.last_name = last_name or student.last_name
            student.academic_unit = academic_unit or student.academic_unit
            student.academic_programme = academic_programme or student.academic_programme
            student.discipline = discipline or student.discipline
            student.specialization = specialization or student.specialization
            student.save()

    return result
