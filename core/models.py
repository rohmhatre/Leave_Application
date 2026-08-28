from django.db import models
from django.contrib.auth.models import AbstractUser


class Student(AbstractUser):
    # username will be the roll number
    roll_number = models.CharField(max_length=20, unique=True)
    ACADEMIC_UNIT_CHOICES = [
        ('Aerospace Department','Aerospace Department'),
        ('Other','Other'),
    ]
    DISCIPLINE_CHOICES = [
        ('Aerospace Engineering','Aerospace Engineering'),
        ('Other','Other'),
    ]
    CATEGORY_CHOICES = [
        ('TA','TA'),
        ('TAP','TAP'),
        ('RA','RA'),
        ('FA','FA'),
    ]
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    academic_unit = models.CharField(max_length=100, choices=ACADEMIC_UNIT_CHOICES, blank=True)
    academic_programme = models.CharField(max_length=100, blank=True)
    discipline = models.CharField(max_length=100, choices=DISCIPLINE_CHOICES, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    category = models.CharField(
        max_length=3,
        choices=CATEGORY_CHOICES,
        blank=True,
        verbose_name='Category of Registration',
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        verbose_name='Gender',
    )
    total_leaves = models.IntegerField(default=15)
    leave_balance = models.IntegerField(default=15)
    first_login = models.BooleanField(default=True)

    USERNAME_FIELD = 'roll_number'
    REQUIRED_FIELDS = ['username', 'email']  # username used for superusers

    def __str__(self):
        return f"{self.roll_number} ({self.get_full_name()})"

    @property
    def leaves_taken(self):
        """Number of leave days approved (used) so far."""
        # sum days for approved applications
        approved = self.leaveapplication_set.filter(status='A')
        total = 0
        for app in approved:
            total += (app.to_date - app.from_date).days + 1
        return total


class LeaveType(models.Model):
    """Different types of leaves available in the system."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3498db', help_text='Hex color code for UI display')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProgrammeLeavePolicy(models.Model):
    """Associates leave types with specific programmes and their allocations."""
    programme = models.CharField(max_length=100)  # e.g., 'MTech', 'PhD', etc.
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    days_allowed = models.IntegerField(default=15, help_text='Number of days allowed for this leave type')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['programme', 'leave_type']
        ordering = ['programme', 'leave_type']

    def __str__(self):
        return f"{self.programme} - {self.leave_type.name} ({self.days_allowed} days)"




class LeaveApplication(models.Model):
    application_number = models.CharField(max_length=20, unique=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    rejection_pdf = models.FileField(upload_to='rejection_pdfs/', blank=True, null=True)
    STIPEND_CHOICES = [
        ('continue', 'My stipend/scholarship from the Institute should be continued during the leave period.'),
        ('not_continue', 'My stipend/scholarship from the Institute need not be continued during the leave period.'),
        ('not_supported', 'I am not supported by a stipend/scholarship from the Institute.'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, null=True, blank=True)
    from_date = models.DateField()
    to_date = models.DateField()
    purpose = models.TextField()
    # free‑text description of where the student intends to visit during the
    # leave period.  added at the user's request so it appears on the form.
    place_of_visit = models.CharField(max_length=255, blank=True)

    faculty_advisor = models.CharField(max_length=100, blank=True)
    thesis_supervisor = models.CharField(max_length=100, blank=True)
    stipend_status = models.CharField(max_length=20, choices=STIPEND_CHOICES, blank=True)

    STATUS_CHOICES = [
        ('P','Pending'),
        ('A','Approved'),
        ('R','Rejected'),
    ]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        leave_info = f" ({self.leave_type.name})" if self.leave_type else ""
        app_num = self.application_number if self.application_number else self.pk
        return f"Leave {app_num} {self.student.roll_number} {self.from_date} to {self.to_date}{leave_info}"

    def save(self, *args, **kwargs):
        if not self.application_number:
            import datetime
            year = datetime.date.today().year
            
            prog_map = {
                'MTech': '1',
                'PhD': '2',
                'MTech+PhD': '3',
                'MSc+PhD': '4'
            }
            prog_code = prog_map.get(self.student.academic_programme, '9')
            
            prefix = f"{year}{prog_code}"
            
            last_app = LeaveApplication.objects.filter(
                application_number__startswith=prefix
            ).order_by('-application_number').first()
            
            if last_app and len(last_app.application_number) >= len(prefix) + 4:
                try:
                    last_seq = int(last_app.application_number[len(prefix):])
                    new_seq = last_seq + 1
                except ValueError:
                    new_seq = 1
            else:
                new_seq = 1
                
            self.application_number = f"{prefix}{new_seq:04d}"
            
        super().save(*args, **kwargs)

# Create your models here.


class ApproverConfig(models.Model):
    """Singleton model: admin controls what the approver panel shows."""

    # Tab visibility
    show_students_tab = models.BooleanField(default=False, verbose_name='Show Students tab')
    show_policies_tab = models.BooleanField(default=False, verbose_name='Show Policies tab')
    show_status_cards = models.BooleanField(default=True, verbose_name='Show status summary cards')
    current_academic_year = models.IntegerField(default=2025, verbose_name='Current Academic Year')

    # Leave Applications — column visibility
    show_app_no = models.BooleanField(default=True, verbose_name='App No')
    show_student_name = models.BooleanField(default=True, verbose_name='Student Name')
    show_roll = models.BooleanField(default=True, verbose_name='Roll Number')
    show_type = models.BooleanField(default=True, verbose_name='Leave Type')
    show_period = models.BooleanField(default=True, verbose_name='Period')
    show_days = models.BooleanField(default=True, verbose_name='Days')
    show_leaves_taken = models.BooleanField(default=True, verbose_name='Leaves Taken')
    show_purpose = models.BooleanField(default=True, verbose_name='Purpose')
    show_status = models.BooleanField(default=True, verbose_name='Status')
    show_submitted = models.BooleanField(default=True, verbose_name='Submitted Date')

    # Leave Applications — action permissions
    can_approve = models.BooleanField(default=True, verbose_name='Can approve applications')
    can_reject = models.BooleanField(default=True, verbose_name='Can reject applications')

    # Students tab — column visibility
    show_stu_name = models.BooleanField(default=True, verbose_name='Student Name')
    show_stu_roll = models.BooleanField(default=True, verbose_name='Roll Number')
    show_stu_gender = models.BooleanField(default=True, verbose_name='Gender')
    show_stu_programme = models.BooleanField(default=True, verbose_name='Programme')
    show_stu_discipline = models.BooleanField(default=True, verbose_name='Discipline')
    show_stu_specialization = models.BooleanField(default=True, verbose_name='Specialization')
    show_stu_taken = models.BooleanField(default=True, verbose_name='Leaves Taken')

    class Meta:
        verbose_name = 'Approver Configuration'
        verbose_name_plural = 'Approver Configuration'

    def save(self, *args, **kwargs):
        # Enforce singleton: always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Approver Panel Configuration'


class BackupConfig(models.Model):
    """Singleton model for backup and restore settings."""
    auto_backup_enabled = models.BooleanField(default=False, verbose_name='Enable Auto-Backup')
    backup_interval_days = models.IntegerField(default=7, verbose_name='Backup Interval (Days)')
    last_backup_at = models.DateTimeField(null=True, blank=True, verbose_name='Last Backup Performed At')

    class Meta:
        verbose_name = 'Backup Configuration'
        verbose_name_plural = 'Backup Configuration'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Backup Configuration'


class StudentLeaveAdjustment(models.Model):
    """Allows manual adjustment of leaves taken for a student."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    adjustment_days = models.IntegerField(default=0, help_text='Add or subtract days from the "taken" count')

    class Meta:
        unique_together = ['student', 'leave_type']

    def __str__(self):
        return f"{self.student.roll_number} - {self.leave_type.name} adjustment: {self.adjustment_days}"
