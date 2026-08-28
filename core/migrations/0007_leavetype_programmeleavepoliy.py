# Generated migration for LeaveType and ProgrammeLeavePolicy models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_leaveapplication_place_of_visit'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaveType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('color', models.CharField(default='#3498db', help_text='Hex color code for UI display', max_length=7)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProgrammeLeavePolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('programme', models.CharField(max_length=100)),
                ('days_allowed', models.IntegerField(default=15, help_text='Number of days allowed for this leave type')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.leavetype')),
            ],
            options={
                'ordering': ['programme', 'leave_type'],
                'unique_together': {('programme', 'leave_type')},
            },
        ),
        migrations.AddField(
            model_name='leaveapplication',
            name='leave_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.leavetype'),
        ),
    ]
