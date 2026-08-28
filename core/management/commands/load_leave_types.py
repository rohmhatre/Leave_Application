from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Load initial leave types and programme policies'

    def handle(self, *args, **options):
        self.stdout.write('Loading initial leave types and policies...')
        try:
            call_command('loaddata', 'initial_leave_types', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ Successfully loaded initial data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error loading data: {str(e)}'))
