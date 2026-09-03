from django.core.management.base import BaseCommand, CommandError

from core.importers import import_students_from_csv


class Command(BaseCommand):
    help = (
        'Import students from a CSV file. Expects columns roll_number, name, '
        'academic_unit, academic_programme, discipline and specialization'
    )

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        path = options['csv_file']
        try:
            with open(path, 'rb') as fh:
                result = import_students_from_csv(fh)
        except FileNotFoundError:
            raise CommandError(f'File not found: {path}')
        except Exception as e:
            raise CommandError(f'Error processing file: {str(e)}')

        skipped = result.skipped_lines
        self.stdout.write(self.style.SUCCESS(
            f'Updated {result.updated} students, created {result.created} new students.'
        ))
        if skipped:
            all_lines = ', '.join(str(n) for n in skipped)
            self.stdout.write(self.style.WARNING(
                f'Skipped {len(skipped)} malformed row(s) with too many '
                f'columns: line {all_lines}.'
            ))
