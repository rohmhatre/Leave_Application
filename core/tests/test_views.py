"""Tests for the student bulk-upload view (``update_students_from_csv``).

The view now reads a CSV file (it used to read XLSX via pandas), so these
tests focus on CSV parsing behaviour and on the failure paths.

The filename does not match Django's default ``test*.py`` discovery pattern,
so run it explicitly:

    python manage.py test core.tests.views_tests
"""

import unittest
from pathlib import Path

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from core.models import Student

DUMMY_CSV = Path(__file__).resolve().parent / 'dummy_students.csv'

# The headers the view actually looks for.
HEADER = 'roll_number,name,academic_unit,academic_programme,discipline,specialization'


class UpdateStudentsFromCSVTests(TestCase):

    def setUp(self):
        self.admin = Student.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            roll_number='ADMIN001',
        )
        self.client.force_login(self.admin)
        self.url = reverse('core:update_students')

    # ---------------- helpers ----------------

    def post_csv(self, content, filename='students.csv'):
        """POST ``content`` (str or bytes) as the uploaded file."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        upload = SimpleUploadedFile(filename, content, content_type='text/csv')
        return self.client.post(self.url, {'csv_file': upload})

    def post_dummy_csv(self):
        with open(DUMMY_CSV, 'rb') as fh:
            return self.post_csv(fh.read(), 'dummy_students.csv')

    def messages_text(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def students(self):
        """Every student created by an upload (excludes the admin from setUp)."""
        return Student.objects.exclude(pk=self.admin.pk)

    # ---------------- 1. happy path with the dummy file ----------------

    def test_upload_dummy_csv_creates_students(self):
        response = self.post_dummy_csv()

        self.assertRedirects(response, reverse('core:admin_panel'))
        self.assertEqual(self.students().count(), 5)
        self.assertIn(
            'Updated 0 students, created 5 new students.',
            self.messages_text(response),
        )

        student = Student.objects.get(roll_number='2023CSE001')
        self.assertEqual(student.username, '2023CSE001')
        self.assertEqual(student.first_name, 'Aarav')
        self.assertEqual(student.last_name, 'Sharma')
        self.assertEqual(student.academic_unit, 'School of Engineering')
        self.assertEqual(student.academic_programme, 'B.Tech')
        self.assertEqual(student.discipline, 'Computer Science')
        self.assertEqual(student.specialization, 'Artificial Intelligence')

    def test_new_student_password_is_the_roll_number(self):
        self.post_dummy_csv()

        student = Student.objects.get(roll_number='2023CSE001')
        self.assertTrue(student.check_password('2023CSE001'))

    def test_multi_word_name_splits_into_first_and_last(self):
        self.post_dummy_csv()

        student = Student.objects.get(roll_number='2023CSE002')
        self.assertEqual(student.first_name, 'Priya')
        self.assertEqual(student.last_name, 'Nair Menon')

    def test_single_word_name_leaves_last_name_empty(self):
        self.post_csv(f'{HEADER}\n2023CSE009,Meera,,,,\n')

        student = Student.objects.get(roll_number='2023CSE009')
        self.assertEqual(student.first_name, 'Meera')
        self.assertEqual(student.last_name, '')

    def test_reupload_updates_instead_of_duplicating(self):
        self.post_dummy_csv()
        response = self.post_dummy_csv()

        self.assertEqual(self.students().count(), 5)
        self.assertIn(
            'Updated 5 students, created 0 new students.',
            self.messages_text(response),
        )

    # ---------------- 3. roll numbers stay strings ----------------

    def test_numeric_roll_number_from_dummy_file_is_a_string(self):
        """The dummy file's numeric roll (2024332021) must stay text.

        The old pandas/XLSX path read such a cell as the float 2024332021.0
        and stored the roll as '2024332021.0'; csv.DictReader hands over text.
        """
        self.post_dummy_csv()

        student = Student.objects.get(roll_number='2024332021')
        self.assertIsInstance(student.roll_number, str)
        self.assertEqual(student.roll_number, '2024332021')
        self.assertEqual(student.username, '2024332021')
        self.assertFalse(Student.objects.filter(roll_number='2024332021.0').exists())

    def test_numeric_roll_number_is_stored_as_string(self):
        self.post_csv(f'{HEADER}\n1001,Numeric Roll,,,,\n')

        student = self.students().get()
        self.assertIsInstance(student.roll_number, str)
        self.assertEqual(student.roll_number, '1001')
        self.assertEqual(student.username, '1001')
        self.assertFalse(Student.objects.filter(roll_number='1001.0').exists())

    def test_leading_zeros_in_roll_number_are_preserved(self):
        self.post_csv(f'{HEADER}\n007,Zero Padded,,,,\n')

        student = self.students().get()
        self.assertEqual(student.roll_number, '007')
        self.assertTrue(Student.objects.filter(roll_number='007').exists())

    def test_roll_number_with_exponent_like_text_is_kept_verbatim(self):
        """'2E3' is a valid roll number, not scientific notation for 2000."""
        self.post_csv(f'{HEADER}\n2E3,Exponent Looking,,,,\n')

        self.assertEqual(self.students().get().roll_number, '2E3')

    def test_numeric_roll_number_matches_only_as_string_on_reupload(self):
        """A numeric roll uploaded twice must update, not create a second row."""
        self.post_csv(f'{HEADER}\n1001,Numeric Roll,,,Physics,\n')
        response = self.post_csv(f'{HEADER}\n1001,Numeric Roll,,,Chemistry,\n')

        self.assertEqual(self.students().count(), 1)
        self.assertEqual(self.students().get().discipline, 'Chemistry')
        self.assertIn(
            'Updated 1 students, created 0 new students.',
            self.messages_text(response),
        )

    # ---------------- 2. failure paths ----------------

    def test_no_file_uploaded_shows_error(self):
        response = self.client.post(self.url, {})

        self.assertRedirects(response, reverse('core:admin_panel'))
        self.assertIn('No file uploaded', self.messages_text(response))
        self.assertEqual(self.students().count(), 0)

    def test_get_request_does_not_import_anything(self):
        """A non-POST request redirects instead of raising (used to be a 500)."""
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('core:admin_panel'))
        self.assertEqual(self.students().count(), 0)

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        response = self.post_dummy_csv()

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(reverse('core:admin_panel'), response['Location'])
        self.assertEqual(self.students().count(), 0)

    def test_non_admin_student_cannot_import(self):
        student = Student.objects.create_user(
            username='2020PHD001',
            email='s@example.com',
            password='pw',
            roll_number='2020PHD001',
        )
        self.client.force_login(student)
        self.post_dummy_csv()

        self.assertEqual(self.students().count(), 1)  # only the logged-in one

    def test_binary_file_reports_error_without_crashing(self):
        """An XLSX (or any non-UTF-8 binary) upload must be reported, not raise."""
        response = self.post_csv(b'PK\x03\x04\xff\xfe\x00\x01binary junk', 'students.xlsx')

        self.assertRedirects(response, reverse('core:admin_panel'))
        errors = [m for m in self.messages_text(response) if m.startswith('Error processing file')]
        self.assertEqual(len(errors), 1)
        self.assertEqual(self.students().count(), 0)

    def test_completely_empty_file_is_handled(self):
        response = self.post_csv(b'')

        self.assertRedirects(response, reverse('core:admin_panel'))
        self.assertEqual(self.students().count(), 0)

    def test_header_only_file_imports_nothing(self):
        response = self.post_csv(f'{HEADER}\n')

        self.assertIn(
            'Updated 0 students, created 0 new students.',
            self.messages_text(response),
        )
        self.assertEqual(self.students().count(), 0)

    def test_rows_without_a_roll_number_are_skipped(self):
        self.post_csv(
            f'{HEADER}\n'
            ',No Roll Here,,,,\n'
            '2023CSE003,Has Roll,,,,\n'
            '   ,Blank Roll,,,,\n'
        )

        self.assertEqual(self.students().count(), 1)
        self.assertEqual(self.students().get().roll_number, '2023CSE003')

    def test_old_xlsx_style_headers_import_nothing(self):
        """Documents current behaviour: only the snake_case headers work.

        A file carrying the pre-CSV headers ('Roll Number', 'NAME') is
        silently accepted and imports zero students.
        """
        response = self.post_csv(
            'Roll Number,NAME,Academic Unit\n'
            '2023CSE004,Old Header,School of Engineering\n'
        )

        self.assertEqual(self.students().count(), 0)
        self.assertIn(
            'Updated 0 students, created 0 new students.',
            self.messages_text(response),
        )

    def test_capitalised_headers_import_nothing(self):
        """Header matching is case-sensitive."""
        response = self.post_csv('Roll_Number,Name\n2023CSE005,Caps Header\n')

        self.assertEqual(self.students().count(), 0)
        self.assertIn(
            'Updated 0 students, created 0 new students.',
            self.messages_text(response),
        )

    # ---------------- corner cases ----------------

    def test_surrounding_whitespace_is_stripped(self):
        self.post_csv(
            ' roll_number , name , discipline \n'
            '  2023CSE006  ,  Anita   Rao  ,  Physics  \n'
        )

        student = self.students().get()
        self.assertEqual(student.roll_number, '2023CSE006')
        self.assertEqual(student.first_name, 'Anita')
        self.assertEqual(student.last_name, 'Rao')
        self.assertEqual(student.discipline, 'Physics')

    def test_utf8_bom_header_is_handled(self):
        """Excel and Google Sheets write a BOM in front of the first header."""
        content = (f'{HEADER}\n2023CSE007,BOM Row,,,,\n').encode('utf-8-sig')
        self.post_csv(content)

        self.assertEqual(self.students().get().roll_number, '2023CSE007')

    def test_crlf_line_endings_are_handled(self):
        content = f'{HEADER}\r\n2023CSE008,CRLF Row,,B.Tech,,\r\n'
        self.post_csv(content)

        student = self.students().get()
        self.assertEqual(student.roll_number, '2023CSE008')
        self.assertEqual(student.academic_programme, 'B.Tech')

    def test_quoted_fields_containing_commas(self):
        content = (
            f'{HEADER}\n'
            '2023CSE011,Ravi Kumar,"School of Engineering, Main Campus",'
            'B.Tech,Computer Science,"AI, ML"\n'
        )
        self.post_csv(content)

        student = self.students().get()
        self.assertEqual(student.academic_unit, 'School of Engineering, Main Campus')
        self.assertEqual(student.specialization, 'AI, ML')

    def test_non_ascii_names_are_preserved(self):
        self.post_csv(f'{HEADER}\n2023CSE012,Zoë Müller,,,,\n')

        student = self.students().get()
        self.assertEqual(student.first_name, 'Zoë')
        self.assertEqual(student.last_name, 'Müller')

    def test_missing_optional_columns_are_tolerated(self):
        self.post_csv('roll_number,name\n2023CSE013,Minimal Columns\n')

        student = self.students().get()
        self.assertEqual(student.first_name, 'Minimal')
        self.assertEqual(student.academic_unit, '')
        self.assertEqual(student.specialization, '')

    def test_extra_unknown_columns_are_ignored(self):
        self.post_csv(
            f'{HEADER},phone,notes\n'
            '2023CSE014,Extra Columns,,,,,9990001111,ignore me\n'
        )

        self.assertEqual(self.students().get().roll_number, '2023CSE014')

    def test_row_with_more_cells_than_headers_is_skipped_and_reported(self):
        """A row carrying data past the last header is not imported."""
        response = self.post_csv(f'{HEADER}\n2023CSE022,Long Row,,,,,extra,cells\n')

        self.assertEqual(self.students().count(), 0)
        self.assertIn(
            'Skipped 1 malformed row(s) with too many columns: line 2.',
            self.messages_text(response),
        )

    def test_unquoted_comma_row_is_skipped_and_its_neighbours_import(self):
        """The realistic source of an over-long row: an unquoted comma.

        'School of Engineering, Main Campus' typed without quotes splits
        into two cells, so every later value would land one column to the
        left.  That row is skipped and named; the rows around it import.
        """
        response = self.post_csv(
            f'{HEADER}\n'
            '2023CSE024,Before The Bad Row,School of Engineering,B.Tech,Computer Science,AI\n'
            '2023CSE025,Rhea Kapoor,School of Engineering, Main Campus,B.Tech,Computer Science,AI\n'
            '2023CSE026,After The Bad Row,School of Engineering,B.Tech,Computer Science,AI\n'
        )

        self.assertEqual(self.students().count(), 2)
        self.assertFalse(Student.objects.filter(roll_number='2023CSE025').exists())

        messages = self.messages_text(response)
        self.assertIn('Updated 0 students, created 2 new students.', messages)
        self.assertIn(
            'Skipped 1 malformed row(s) with too many columns: line 3.',
            messages,
        )

        # the rows on either side are untouched
        for roll in ('2023CSE024', '2023CSE026'):
            neighbour = Student.objects.get(roll_number=roll)
            self.assertEqual(neighbour.academic_unit, 'School of Engineering')
            self.assertEqual(neighbour.academic_programme, 'B.Tech')
            self.assertEqual(neighbour.discipline, 'Computer Science')
            self.assertEqual(neighbour.specialization, 'AI')

    def test_trailing_commas_are_skipped_as_malformed(self):
        """Surplus cells are rejected even when they are empty.

        The row still has the wrong shape, so it is not trusted.
        """
        response = self.post_csv(f'{HEADER}\n2023CSE028,Trailing Commas,,,,,,,\n')

        self.assertEqual(self.students().count(), 0)
        self.assertIn(
            'Skipped 1 malformed row(s) with too many columns: line 2.',
            self.messages_text(response),
        )

    def test_correct_cell_count_with_empty_trailing_fields_still_imports(self):
        """A row that merely leaves optional columns blank is fine."""
        response = self.post_csv(f'{HEADER}\n2023CSE032,Blank Tail,,,,\n')

        student = self.students().get()
        self.assertEqual(student.roll_number, '2023CSE032')
        self.assertEqual(student.specialization, '')
        warnings = [m for m in self.messages_text(response) if m.startswith('Skipped')]
        self.assertEqual(warnings, [])

    def test_skipped_lines_are_logged(self):
        """One summary record per import, listing every skipped line."""
        with self.assertLogs('core.views', level='WARNING') as captured:
            self.post_csv(
                f'{HEADER}\n'
                '2023CSE033,Bad One,School of Engineering, Main Campus,B.Tech,CS,AI\n'
                '2023CSE034,Good One,School of Engineering,B.Tech,CS,AI\n'
                '2023CSE035,Bad Two,School of Sciences, North Wing,Ph.D.,Physics,Optics\n'
            )

        self.assertEqual(len(captured.records), 1)
        self.assertEqual(
            captured.output[0],
            "WARNING:core.views:Skipped 2 malformed row(s) in 'students.csv': "
            "line(s) 2, 4",
        )

    def test_log_lists_more_skipped_lines_than_the_message_shows(self):
        """The on-screen warning caps its list at 10; the log does not."""
        rows = ''.join(
            f'2023BAD{i:03d},Bad Row,School of Engineering, Main Campus,B.Tech,CS,AI\n'
            for i in range(12)
        )
        with self.assertLogs('core.views', level='WARNING') as captured:
            self.post_csv(f'{HEADER}\n{rows}')

        self.assertEqual(
            captured.output[0],
            "WARNING:core.views:Skipped 12 malformed row(s) in 'students.csv': "
            "line(s) 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13",
        )

    def test_a_failed_import_is_logged_with_a_traceback(self):
        """The except branch records what the admin only sees as a message."""
        Student.objects.create(roll_number='2020PHD078', username='2023CSE036')

        with self.assertLogs('core.views', level='ERROR') as captured:
            self.post_csv(f'{HEADER}\n2023CSE036,Clashing Username,,,,\n')

        self.assertEqual(len(captured.records), 1)
        record = captured.records[0]
        self.assertEqual(record.levelname, 'ERROR')
        self.assertIn(
            'Failed to import students from file: students.csv',
            record.getMessage(),
        )
        # the message names only the file; the cause rides along in the traceback
        self.assertIsNotNone(record.exc_info)
        self.assertIn('UNIQUE constraint failed', str(record.exc_info[1]))

    def test_nothing_is_logged_for_a_clean_file(self):
        with self.assertNoLogs('core.views', level='WARNING'):
            self.post_dummy_csv()

    def test_several_malformed_rows_are_all_listed(self):
        response = self.post_csv(
            f'{HEADER}\n'
            '2023CSE029,Bad One,School of Engineering, Main Campus,B.Tech,CS,AI\n'
            '2023CSE030,Good One,School of Engineering,B.Tech,CS,AI\n'
            '2023CSE031,Bad Two,School of Sciences, North Wing,Ph.D.,Physics,Optics\n'
        )

        self.assertEqual(self.students().count(), 1)
        self.assertEqual(self.students().get().roll_number, '2023CSE030')
        self.assertIn(
            'Skipped 2 malformed row(s) with too many columns: line 2, 4.',
            self.messages_text(response),
        )

    def test_skipped_line_list_is_capped_at_ten(self):
        rows = ''.join(
            f'2023BAD{i:03d},Bad Row,School of Engineering, Main Campus,B.Tech,CS,AI\n'
            for i in range(12)
        )
        response = self.post_csv(f'{HEADER}\n{rows}')

        self.assertEqual(self.students().count(), 0)
        self.assertIn(
            'Skipped 12 malformed row(s) with too many columns: '
            'line 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 and 2 more.',
            self.messages_text(response),
        )

    def test_a_failing_row_does_not_leave_a_partial_import(self):
        """The import is atomic: a row that raises rolls the whole file back.

        The middle row's roll number is already in use as another student's
        username, so creating it raises IntegrityError (username is unique).
        The good row before it must not survive either.
        """
        Student.objects.create(roll_number='2020PHD077', username='2023CSE027')

        response = self.post_csv(
            f'{HEADER}\n'
            'GOOD001,Good Row,,,,\n'
            '2023CSE027,Clashing Username,,,,\n'
            'GOOD002,After The Bad Row,,,,\n'
        )

        # only the student created above survives; nothing was imported
        self.assertEqual(self.students().count(), 1)
        self.assertFalse(Student.objects.filter(roll_number='GOOD001').exists())
        self.assertFalse(Student.objects.filter(roll_number='GOOD002').exists())
        errors = [m for m in self.messages_text(response) if m.startswith('Error processing file')]
        self.assertEqual(len(errors), 1)

    def test_short_row_with_missing_trailing_values(self):
        """A row with fewer cells than headers must not raise."""
        self.post_csv(f'{HEADER}\n2023CSE015,Short Row\n')

        student = self.students().get()
        self.assertEqual(student.first_name, 'Short')
        self.assertEqual(student.specialization, '')

    def test_blank_cells_do_not_wipe_existing_values(self):
        Student.objects.create(
            roll_number='2023CSE016',
            username='2023CSE016',
            first_name='Old',
            last_name='Name',
            academic_programme='PhD',
            discipline='Physics',
            specialization='Optics',
        )
        self.post_csv(f'{HEADER}\n2023CSE016,,,,,\n')

        student = Student.objects.get(roll_number='2023CSE016')
        self.assertEqual(student.first_name, 'Old')
        self.assertEqual(student.last_name, 'Name')
        self.assertEqual(student.academic_programme, 'PhD')
        self.assertEqual(student.discipline, 'Physics')
        self.assertEqual(student.specialization, 'Optics')

    def test_existing_student_fields_are_overwritten_when_present(self):
        Student.objects.create(
            roll_number='2023CSE017',
            username='2023CSE017',
            first_name='Old',
            last_name='Name',
            discipline='Physics',
        )
        response = self.post_csv(f'{HEADER}\n2023CSE017,New Name,,,Chemistry,\n')

        student = Student.objects.get(roll_number='2023CSE017')
        self.assertEqual(student.first_name, 'New')
        self.assertEqual(student.last_name, 'Name')
        self.assertEqual(student.discipline, 'Chemistry')
        self.assertIn(
            'Updated 1 students, created 0 new students.',
            self.messages_text(response),
        )

    def test_existing_student_password_is_not_reset_on_update(self):
        student = Student.objects.create(roll_number='2023CSE018', username='2023CSE018')
        student.set_password('original-password')
        student.save()

        self.post_csv(f'{HEADER}\n2023CSE018,Some Name,,,,\n')

        student.refresh_from_db()
        self.assertTrue(student.check_password('original-password'))

    def test_existing_student_leave_balance_is_not_reset(self):
        Student.objects.create(
            roll_number='2023CSE023',
            username='2023CSE023',
            total_leaves=20,
            leave_balance=7,
        )
        self.post_csv(f'{HEADER}\n2023CSE023,Some Name,,,,\n')

        student = Student.objects.get(roll_number='2023CSE023')
        self.assertEqual(student.total_leaves, 20)
        self.assertEqual(student.leave_balance, 7)

    def test_duplicate_roll_number_in_same_file_keeps_last_row(self):
        response = self.post_csv(
            f'{HEADER}\n'
            '2023CSE019,First Row,,,Physics,\n'
            '2023CSE019,Second Row,,,Chemistry,\n'
        )

        self.assertEqual(self.students().count(), 1)
        student = self.students().get()
        self.assertEqual(student.first_name, 'Second')
        self.assertEqual(student.discipline, 'Chemistry')
        # The same student is counted twice: once created, once updated.
        self.assertIn(
            'Updated 1 students, created 1 new students.',
            self.messages_text(response),
        )

    def test_blank_lines_between_rows_are_skipped(self):
        self.post_csv(
            f'{HEADER}\n'
            '2023CSE020,Row One,,,,\n'
            '\n'
            '2023CSE021,Row Two,,,,\n'
        )

        self.assertEqual(self.students().count(), 2)

    def test_admin_account_is_untouched_by_import(self):
        self.post_dummy_csv()

        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser)
        self.assertTrue(self.admin.check_password('adminpass'))
