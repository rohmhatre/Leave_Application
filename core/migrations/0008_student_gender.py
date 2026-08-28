# Generated migration for adding gender field to Student model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_leavetype_programmeleavepoliy'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='gender',
            field=models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female')], max_length=1, verbose_name='Gender'),
        ),
    ]