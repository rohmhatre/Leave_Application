from django.core.management.base import BaseCommand
import pandas as pd
from core.models import Student


class Command(BaseCommand):
    help = 'Import students from an Excel file. Expects columns NAME and Roll Number'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        path = options['excel_file']
        df = pd.read_excel(path)
        for idx, row in df.iterrows():
            name = row.get('NAME') or ''
            roll = row.get('Roll Number') or row.get('Roll') or ''
            if not roll:
                continue
            academic_unit = row.get('Academic Unit','')
            academic_programme = row.get('Academic Programme','')
            discipline = row.get('Discipline','')
            specialization = row.get('Specialization','')
            first_name = ''
            last_name = ''
            parts = str(name).split()
            if parts:
                first_name = parts[0]
                if len(parts) > 1:
                    last_name = ' '.join(parts[1:])
            user, created = Student.objects.get_or_create(
                roll_number=roll,
                defaults={'username': roll}
            )
            if created:
                user.first_name = first_name
                user.last_name = last_name
                user.academic_unit = academic_unit
                user.academic_programme = academic_programme
                user.discipline = discipline
                user.specialization = specialization
                # set initial password same as roll
                user.set_password(roll)
                # leave allotment defaults
                user.total_leaves = 15
                user.leave_balance = 15
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created {roll}'))
            else:
                # skip existing students without modifying them
                self.stdout.write(f'Skipped (already exists): {roll}')
