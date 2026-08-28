from django.core.management.base import BaseCommand
from core.models import Student, LeaveType, ProgrammeLeavePolicy
from datetime import date

class Command(BaseCommand):
    help = 'Manually allocate or expire periodic leaves for selected leave types.'

    def add_arguments(self, parser):
        parser.add_argument('--programme', type=str, help='Programme name (e.g., MTech)')
        parser.add_argument('--leave_type', type=str, help='Leave type name (e.g., Casual Leave)')
        parser.add_argument('--action', type=str, choices=['allocate', 'expire'], required=True, help='Action to perform: allocate or expire')

    def handle(self, *args, **options):
        programme = options['programme']
        leave_type_name = options['leave_type']
        action = options['action']

        leave_type = LeaveType.objects.filter(name=leave_type_name).first()
        if not leave_type:
            self.stdout.write(self.style.ERROR(f'Leave type "{leave_type_name}" not found.'))
            return

        students = Student.objects.filter(academic_programme=programme)
        if not students.exists():
            self.stdout.write(self.style.ERROR(f'No students found for programme "{programme}".'))
            return

        if action == 'allocate':
            for student in students:
                student.leave_balance += 15  # Add 15 leaves to the current balance
                student.save()
            self.stdout.write(self.style.SUCCESS(f'Added 15 leaves to {students.count()} students in {programme} for leave type {leave_type_name}.'))
        elif action == 'expire':
            policy = ProgrammeLeavePolicy.objects.filter(programme=programme, leave_type=leave_type, is_active=True).first()
            if not policy:
                self.stdout.write(self.style.ERROR(f'No active policy found for {programme} and {leave_type_name}.'))
                return
            for student in students:
                student.leave_balance = policy.days_allowed  # Reset to policy value
                student.save()
            self.stdout.write(self.style.SUCCESS(f'Reset leave balance to {policy.days_allowed} for {students.count()} students in {programme} for leave type {leave_type_name}.'))
