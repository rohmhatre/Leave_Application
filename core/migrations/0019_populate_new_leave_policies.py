from django.db import migrations

def populate_policies(apps, schema_editor):
    LeaveType = apps.get_model('core', 'LeaveType')
    ProgrammeLeavePolicy = apps.get_model('core', 'ProgrammeLeavePolicy')

    # 1. Update/Create Leave Types
    leave_types_data = [
        {'id': 1, 'name': 'Casual Leave', 'description': 'Regular casual leave for personal reasons', 'color': '#3498db'},
        {'id': 2, 'name': 'Maternity Leave', 'description': 'Maternity leave for female students', 'color': '#e74c3c'},
        {'id': 3, 'name': 'Paternity Leave', 'description': 'Paternity leave for male students', 'color': '#f39c12'},
        {'id': 4, 'name': 'Sick Leave', 'description': 'Medical or illness related leave', 'color': '#e67e22'},
        {'id': 5, 'name': 'Special Leave', 'description': 'Special leave to attend seminar/conference', 'color': '#27ae60'},
        {'id': 6, 'name': 'Vacation Leave', 'description': 'Winter/summer vacation in their 1st year', 'color': '#9b59b6'},
    ]

    for lt_info in leave_types_data:
        lt, created = LeaveType.objects.get_or_create(id=lt_info['id'])
        lt.name = lt_info['name']
        lt.description = lt_info['description']
        lt.color = lt_info['color']
        lt.is_active = True
        lt.save()

    # 2. Delete existing policies to start fresh
    ProgrammeLeavePolicy.objects.all().delete()

    # 3. Create new Policies
    policies_data = [
        # MTech
        {'programme': 'MTech', 'leave_type_id': 1, 'days_allowed': 30},
        {'programme': 'MTech', 'leave_type_id': 5, 'days_allowed': 5},
        {'programme': 'MTech', 'leave_type_id': 6, 'days_allowed': 15},
        # PhD
        {'programme': 'PhD', 'leave_type_id': 1, 'days_allowed': 30},
        {'programme': 'PhD', 'leave_type_id': 4, 'days_allowed': 10},
        {'programme': 'PhD', 'leave_type_id': 2, 'days_allowed': 180},
        {'programme': 'PhD', 'leave_type_id': 3, 'days_allowed': 15},
        {'programme': 'PhD', 'leave_type_id': 5, 'days_allowed': 30},
    ]

    for p_info in policies_data:
        ProgrammeLeavePolicy.objects.create(
            programme=p_info['programme'],
            leave_type_id=p_info['leave_type_id'],
            days_allowed=p_info['days_allowed'],
            is_active=True
        )

def rollback_policies(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_studentleaveadjustment'),
    ]

    operations = [
        migrations.RunPython(populate_policies, rollback_policies),
    ]
