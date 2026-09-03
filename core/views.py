from django.views.decorators.http import require_POST
from django.db import models
from django.db.models import ProtectedError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from .models import LeaveApplication, Student, LeaveType, ProgrammeLeavePolicy, ApproverConfig, BackupConfig, StudentLeaveAdjustment
from .importers import import_students_from_csv
from django import forms
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, FileResponse
from django.core import management
from django.utils import timezone
import subprocess
import os
import json
import logging
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)

# Utility function to check if user is admin
def is_admin(user):
    return user.is_superuser

# Admin: Reset leave balances for a policy
@login_required
@user_passes_test(is_admin)
@require_POST
def reset_policy(request, pk):
    policy = get_object_or_404(ProgrammeLeavePolicy, pk=pk)
    # Find all students in this programme
    students = Student.objects.filter(academic_programme=policy.programme)
    # For each student, remove all APPROVED applications for this leave type (or mark as reset/cancelled if you want to keep history)
    for student in students:
        LeaveApplication.objects.filter(student=student, leave_type=policy.leave_type, status='A').delete()
    messages.success(request, f"All approved leaves for {policy.leave_type.name} in {policy.programme} have been reset.")
    return redirect('core:admin_panel')

# ...existing code...

@login_required
@user_passes_test(is_admin)
def delete_leave_type(request, pk):
    leave_type = get_object_or_404(LeaveType, pk=pk)
    # Prevent deletion if referenced by any ProgrammeLeavePolicy or LeaveApplication
    if ProgrammeLeavePolicy.objects.filter(leave_type=leave_type).exists():
        messages.error(request, 'Cannot delete: Leave type is used in programme policies.')
        return redirect('core:admin_panel')
    if LeaveApplication.objects.filter(leave_type=leave_type).exists():
        messages.error(request, 'Cannot delete: Leave type is used in leave applications.')
        return redirect('core:admin_panel')
    leave_type.delete()
    messages.success(request, f'Leave type "{leave_type.name}" deleted successfully.')
    return redirect('core:admin_panel')

class ProfileForm(forms.ModelForm):
    PROGRAMME_CHOICES = [
        ('', '---------'),
        ('MTech', 'MTech'),
        ('PhD', 'PhD'),
        ('MTech+PhD', 'MTech+PhD'),
        ('MSc+PhD', 'MSc+PhD'),
        ('Other', 'Other (please specify)'),
    ]
    SPECIALIZATION_CHOICES = [
        ('', '---------'),
        ('Aerodynamics','Aerodynamics'),
        ('Propulsion','Propulsion'),
        ('Structure','Structure'),
        ('Dynamics and controls','Dynamics and controls'),
        ('Other','Other (please specify)'),
    ]

    academic_programme = forms.CharField(required=False)
    academic_programme_choice = forms.ChoiceField(choices=PROGRAMME_CHOICES, required=False)

    specialization = forms.CharField(required=False)
    specialization_choice = forms.ChoiceField(choices=SPECIALIZATION_CHOICES, required=False)

    class Meta:
        model = Student
        fields = [
            'first_name','last_name','gender','academic_unit','category',
            'academic_programme','discipline','specialization'
        ]
        widgets = {
            'gender': forms.Select(choices=Student.GENDER_CHOICES),
            'academic_unit': forms.Select(choices=Student.ACADEMIC_UNIT_CHOICES),
            'category': forms.Select(choices=Student.CATEGORY_CHOICES),
            'academic_programme': forms.TextInput(attrs={'style':'display:none;'}),
            'discipline': forms.Select(choices=Student.DISCIPLINE_CHOICES),
            'specialization': forms.TextInput(attrs={'style':'display:none;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if existing programme not in choices, set custom
        val = self.instance.academic_programme
        if val and val not in dict(self.PROGRAMME_CHOICES):
            self.fields['academic_programme_choice'].initial = 'Other'
            self.fields['academic_programme'].initial = val
        else:
            self.fields['academic_programme_choice'].initial = val
        sval = getattr(self.instance,'specialization','')
        if sval and sval not in dict(self.SPECIALIZATION_CHOICES):
            self.fields['specialization_choice'].initial = 'Other'
            self.fields['specialization'].initial = sval
        else:
            self.fields['specialization_choice'].initial = sval

    def clean(self):
        cleaned = super().clean()
        choice = cleaned.get('academic_programme_choice')
        custom = cleaned.get('academic_programme')
        if choice=='Other':
            cleaned['academic_programme'] = custom
        else:
            cleaned['academic_programme'] = choice
        # specialization
        schoice = cleaned.get('specialization_choice')
        scustom = cleaned.get('specialization')
        if schoice=='Other':
            cleaned['specialization'] = scustom
        else:
            cleaned['specialization'] = schoice
        return cleaned


class LeaveForm(forms.ModelForm):

    PROFESSOR_CHOICES = [
        ('', '---------'),
        ('Prof. Avijit Chatterjee', 'Prof. Avijit Chatterjee'),
        ('Prof. J.C. Mandal', 'Prof. J.C. Mandal'),
        ('Prof. V. Menezes', 'Prof. V. Menezes'),
        ('Prof. Vineeth Nair', 'Prof. Vineeth Nair'),
        ('Prof. R. K. Pant', 'Prof. R. K. Pant'),
        ('Prof. Prabhu Ramachandran', 'Prof. Prabhu Ramachandran'),
        ('Prof. Dhwanil Shukla', 'Prof. Dhwanil Shukla'),
        ('Prof. Aniruddha Sinha', 'Prof. Aniruddha Sinha'),
        ('Prof. Hemendra Arya', 'Prof. Hemendra Arya'),
        ('Prof. Rohit Gupta', 'Prof. Rohit Gupta'),
        ('Prof. Shashi Ranjan Kumar', 'Prof. Shashi Ranjan Kumar'),
        ('Prof. Arnab Maity', 'Prof. Arnab Maity'),
        ('Prof. Rohit V. Nanavati', 'Prof. Rohit V. Nanavati'),
        ('Prof. A. M. Pradeep', 'Prof. A. M. Pradeep'),
        ('Prof. Kowsik Bodi', 'Prof. Kowsik Bodi'),
        ('Prof. T. Chandra Sekar', 'Prof. T. Chandra Sekar'),
        ('Prof. Hrishikesh Gadgil', 'Prof. Hrishikesh Gadgil'),
        ('Prof. Sudarshan Kumar', 'Prof. Sudarshan Kumar'),
        ('Prof. Nagendra Kumar', 'Prof. Nagendra Kumar'),
        ('Dr. V. Venkateswara Rao', 'Dr. V. Venkateswara Rao'),
        ('Prof. K. Sinha', 'Prof. K. Sinha'),
        ('Prof. Abhijit Gogulapati', 'Prof. Abhijit Gogulapati'),
        ('Prof. P J Guruprasad', 'Prof. P J Guruprasad'),
        ('Prof. Krishnendu Haldar', 'Prof. Krishnendu Haldar'),
        ('Prof. Chandra Sekher Yerramalli', 'Prof. Chandra Sekher Yerramalli'),
    ]

    faculty_advisor = forms.ChoiceField(
        choices=PROFESSOR_CHOICES,
        required=False,
        label='Faculty Advisor',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    thesis_supervisor = forms.ChoiceField(
        choices=PROFESSOR_CHOICES,
        required=False,
        label='Thesis Supervisor',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = LeaveApplication
        fields = [
            'leave_type', 'from_date', 'to_date', 'purpose', 'place_of_visit',
            'stipend_status', 'faculty_advisor', 'thesis_supervisor'
        ]
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'place_of_visit': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'stipend_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter leave types based on student's programme and gender
        if student and student.academic_programme:
            policies = ProgrammeLeavePolicy.objects.filter(
                programme=student.academic_programme,
                is_active=True,
                leave_type__is_active=True
            ).select_related('leave_type')
            
            # Filter by gender for maternity/paternity leaves
            leave_types = []
            for policy in policies:
                leave_type = policy.leave_type
                # Maternity leave only for females
                if leave_type.name.lower() == 'maternity leave' and student.gender != 'F':
                    continue
                # Paternity leave only for males
                if leave_type.name.lower() == 'paternity leave' and student.gender != 'M':
                    continue
                leave_types.append(leave_type)
            
            if leave_types:
                self.fields['leave_type'].queryset = LeaveType.objects.filter(
                    id__in=[lt.id for lt in leave_types]
                )
            else:
                # Fallback: show all active leave types if no programme-specific policy found
                self.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)
        else:
            self.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)
        
        self.fields['leave_type'].required = True
        self.fields['leave_type'].label = 'Type of Leave'


def student_login(request):
    # kept for compatibility but landing page will handle actual login
    return redirect('core:landing')


def admin_login(request):
    """Separate admin login page that only allows superuser authentication."""
    # admin login handled on landing; keep route for compatibility
    return redirect('core:landing')


def student_logout(request):
    logout(request)
    return redirect('core:landing')


def landing(request):
    """Public landing page with two login sections: student and admin."""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        login_type = request.POST.get('login_type')
        roll = request.POST.get('roll_number')
        pwd = request.POST.get('password')
        if roll:
            roll = roll.strip()
            db_user = Student.objects.filter(roll_number__iexact=roll).first()
            if db_user:
                roll = db_user.roll_number
        user = authenticate(request, roll_number=roll, password=pwd)
        if user is None:
            messages.error(request, 'Invalid credentials')
            return render(request, 'core/landing.html')

        if login_type == 'student':
            # ensure not superuser
            if user.is_superuser:
                messages.error(request, 'Please use Admin section for admin accounts')
                return render(request, 'core/landing.html')
            login(request, user)
            if user.first_login:
                return redirect('core:change_password')
            if not user.academic_unit or not user.academic_programme or not user.discipline:
                return redirect('core:change_password')
            return redirect('core:home')

        if login_type == 'approver':
            if not user.is_staff or user.is_superuser:
                messages.error(request, 'Invalid approver credentials')
                return render(request, 'core/landing.html')
            login(request, user)
            return redirect('core:approver_panel')

        if login_type == 'admin':
            # only allow superusers to log in via admin card
            if not user.is_superuser:
                messages.error(request, 'Invalid admin credentials')
                return render(request, 'core/landing.html')
            login(request, user)
            return redirect('core:admin_panel')

    return render(request, 'core/landing.html')


def get_leave_type_balances(student, leave_type, policy):
    """
    Calculates the days allowed and remaining days for a specific student and leave type,
    applying custom program-specific policies (MTech Vacation Leave, PhD Sick/Casual Leave carry-over).
    """
    from core.models import ApproverConfig
    config = ApproverConfig.load()
    current_acad_year = config.current_academic_year
    days_allowed = policy.days_allowed if policy else 0
    
    # Define current academic year of study
    try:
        admission_year = 2000 + int(student.roll_number[:2])
    except (ValueError, TypeError, IndexError):
        admission_year = student.date_joined.year if student.date_joined else current_acad_year
        
    years_of_study = max(1, current_acad_year - admission_year + 1)
    
    lt_name = leave_type.name.lower() if leave_type else ''
    prog = student.academic_programme
    
    # 1. Custom MTech Vacation Leave Rule
    if prog == 'MTech' and 'vacation' in lt_name:
        if years_of_study == 1:
            days_allowed = 15
        else:
            days_allowed = 0
        
        # Calculate taken Vacation Leaves
        approved_leaves = LeaveApplication.objects.filter(
            student=student,
            leave_type=leave_type,
            status='A'
        )
        total_days = sum((app.to_date - app.from_date).days + 1 for app in approved_leaves)
        
        adj = StudentLeaveAdjustment.objects.filter(student=student, leave_type=leave_type).first()
        if adj:
            total_days += adj.adjustment_days
            
        remaining = max(days_allowed - total_days, 0)
        return days_allowed, remaining
        
    # 2. Custom PhD Sick Leave (Medical Leave) and Casual Leave Carry-over Rule
    if prog == 'PhD' and ('sick' in lt_name or 'casual' in lt_name):
        annual_allocation = 10 if 'sick' in lt_name else 30
        
        approved_leaves = LeaveApplication.objects.filter(
            student=student,
            leave_type=leave_type,
            status='A'
        ).order_by('from_date')
        
        taken_per_year = {}
        for app in approved_leaves:
            days = (app.to_date - app.from_date).days + 1
            fd = app.from_date
            yr = (fd.year - 1 if fd.month < 7 else fd.year) - admission_year + 1
            yr = max(1, yr)
            taken_per_year[yr] = taken_per_year.get(yr, 0) + days
            
        # Add adjustment to the current year
        adj = StudentLeaveAdjustment.objects.filter(student=student, leave_type=leave_type).first()
        if adj:
            taken_per_year[years_of_study] = taken_per_year.get(years_of_study, 0) + adj.adjustment_days
            
        # Recurrence to calculate remaining and allowed for each year
        prev_remaining = 0
        current_allowed = annual_allocation
        current_remaining = annual_allocation
        
        for k in range(1, years_of_study + 1):
            if k == 1:
                allowed = annual_allocation
            else:
                allowed = min(prev_remaining + annual_allocation, 90)
            
            taken = taken_per_year.get(k, 0)
            prev_remaining = max(allowed - taken, 0)
            
            if k == years_of_study:
                current_allowed = allowed
                current_remaining = prev_remaining
                
        return current_allowed, current_remaining

    # 3. Standard Balance Logic
    approved_leaves = LeaveApplication.objects.filter(
        student=student,
        leave_type=leave_type,
        status='A'
    )
    if prog == 'MTech':
        # Renewed to original with no carry-forward: only count leaves taken in the current academic year
        current_year_leaves = []
        for app in approved_leaves:
            fd = app.from_date
            yr = (fd.year - 1 if fd.month < 7 else fd.year) - admission_year + 1
            yr = max(1, yr)
            if yr == years_of_study:
                current_year_leaves.append(app)
        approved_leaves = current_year_leaves
        
    total_days = sum((app.to_date - app.from_date).days + 1 for app in approved_leaves)
    
    adj = StudentLeaveAdjustment.objects.filter(student=student, leave_type=leave_type).first()
    if adj:
        total_days += adj.adjustment_days
        
    remaining = max(days_allowed - total_days, 0)
    return days_allowed, remaining


@login_required
def home(request):
    # student dashboard
    if request.user.is_superuser:
        return redirect('core:admin_panel')
    user = request.user
    if user.first_login:
        return redirect('core:change_password')
    if not user.academic_unit or not user.academic_programme or not user.discipline:
        return redirect('core:change_password')
    # include this student's applications for status tab
    applications = LeaveApplication.objects.filter(student=user).order_by('-submitted_at')

    # Get leave types and allowed days for this student's programme, filter by gender
    policies = ProgrammeLeavePolicy.objects.filter(
        programme=user.academic_programme,
        is_active=True,
        leave_type__is_active=True
    ).select_related('leave_type')
    leave_type_policies = []
    for p in policies:
        lt = p.leave_type
        # Maternity leave only for females
        if lt.name.lower() == 'maternity leave' and user.gender != 'F':
            continue
        # Paternity leave only for males
        if lt.name.lower() == 'paternity leave' and user.gender != 'M':
            continue
        
        days_allowed, remaining = get_leave_type_balances(user, lt, p)
        leave_type_policies.append((lt, days_allowed, remaining))

    # Render the student dashboard template
    return render(request, 'core/home.html', {
        'applications': applications,
        'leave_type_policies': leave_type_policies,
        'user': user,
    })


@login_required
def apply_leave(request):
    user = request.user
    # Prepare leave type remaining dict
    policies = ProgrammeLeavePolicy.objects.filter(
        programme=user.academic_programme,
        is_active=True,
        leave_type__is_active=True
    ).select_related('leave_type')
    leave_type_remaining = {}
    for p in policies:
        lt = p.leave_type
        # Maternity leave only for females
        if lt.name.lower() == 'maternity leave' and user.gender != 'F':
            continue
        # Paternity leave only for males
        if lt.name.lower() == 'paternity leave' and user.gender != 'M':
            continue
        _, remaining = get_leave_type_balances(user, lt, p)
        leave_type_remaining[lt.id] = remaining

    if request.method == 'POST':
        form = LeaveForm(request.POST, student=user)
        if form.is_valid():
            leave = form.save(commit=False)
            days = (leave.to_date - leave.from_date).days + 1
            if days <= 0:
                messages.error(request, 'Invalid date range')
            elif leave.leave_type and days > leave_type_remaining.get(leave.leave_type.id, 0):
                messages.error(request, f'Insufficient leave balance for {leave.leave_type.name}')
            else:
                # Custom Leave Rules Validations
                if leave.leave_type:
                    lt_name = leave.leave_type.name.lower()
                    
                    # 1. MTech Vacation Leave only in 1st year
                    if user.academic_programme == 'MTech' and 'vacation' in lt_name:
                        fd = leave.from_date
                        try:
                            admission_year = 2000 + int(user.roll_number[:2])
                        except (ValueError, TypeError, IndexError):
                            admission_year = user.date_joined.year if user.date_joined else fd.year
                        leave_acad_year = (fd.year - 1 if fd.month < 7 else fd.year) - admission_year + 1
                        if leave_acad_year > 1:
                            messages.error(request, 'Vacation leave is only allowed in your 1st year.')
                            return render(request, 'core/apply_leave.html', {
                                'form': form,
                                'leave_type_remaining': leave_type_remaining
                            })
                            
                    # 2. PhD Maternity Leave once in studentship
                    if user.academic_programme == 'PhD' and 'maternity' in lt_name:
                        existing = LeaveApplication.objects.filter(
                            student=user,
                            leave_type=leave.leave_type,
                            status__in=['A', 'P']
                        ).exclude(pk=leave.pk)
                        if existing.exists():
                            messages.error(request, 'Maternity leave can only be taken once during the tenure of studentship.')
                            return render(request, 'core/apply_leave.html', {
                                'form': form,
                                'leave_type_remaining': leave_type_remaining
                            })
                            
                    # 3. PhD Paternity Leave once in award
                    if user.academic_programme == 'PhD' and 'paternity' in lt_name:
                        existing = LeaveApplication.objects.filter(
                            student=user,
                            leave_type=leave.leave_type,
                            status__in=['A', 'P']
                        ).exclude(pk=leave.pk)
                        if existing.exists():
                            messages.error(request, 'Paternity leave can only be taken once during the tenure of the award.')
                            return render(request, 'core/apply_leave.html', {
                                'form': form,
                                'leave_type_remaining': leave_type_remaining
                            })

                # Validate against leave type policy for the student's programme
                if leave.leave_type:
                    policy = ProgrammeLeavePolicy.objects.filter(
                        programme=user.academic_programme,
                        leave_type=leave.leave_type,
                        is_active=True
                    ).first()
                    
                    if user.academic_programme == 'PhD' and ('sick' in leave.leave_type.name.lower() or 'casual' in leave.leave_type.name.lower()):
                        allowed, _ = get_leave_type_balances(user, leave.leave_type, policy)
                    else:
                        allowed = policy.days_allowed if policy else 0
                        
                    if policy and days > allowed:
                        messages.error(
                            request,
                            f'Leave type "{leave.leave_type.name}" allows maximum {allowed} days. '
                            f'You requested {days} days.'
                        )
                        return render(request, 'core/apply_leave.html', {
                            'form': form,
                            'leave_type_remaining': leave_type_remaining
                        })
                leave.student = user
                leave.save()
                messages.success(request, f'Applied for {days} day(s) leave (pending approval)')
                return redirect('core:view_application', pk=leave.pk)
    else:
        form = LeaveForm(student=user)
    return render(request, 'core/apply_leave.html', {'form': form, 'leave_type_remaining': leave_type_remaining})


@login_required
def view_application(request, pk):
    leave = get_object_or_404(LeaveApplication, pk=pk, student=request.user)
    return render(request, 'core/view_application.html', {'leave': leave})


@login_required
def download_application_pdf(request, pk):
    """Fill and download leave application PDF by overlaying data."""
    import os
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    from django.http import FileResponse
    from django.conf import settings
    
    # Admins can download any application; students only their own
    if request.user.is_superuser:
        leave = get_object_or_404(LeaveApplication, pk=pk)
    else:
        leave = get_object_or_404(LeaveApplication, pk=pk, student=request.user)
    
    # Path to template PDF
    template_pdf = os.path.join(settings.BASE_DIR, 'Official_acad_leave_2901014.pdf')
    
    # If template PDF exists, overlay data
    if os.path.exists(template_pdf):
        try:
            # Create overlay with student data
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont('Helvetica-Bold', 10)
            
            # Application number and type of leave (adjust coordinates as needed)
            can.setFont('Helvetica-Bold', 10)
            can.drawString(30, 760, f"Application No: {leave.application_number}")
            can.drawString(500, 553, f": {leave.leave_type.name if leave.leave_type else ''}")
            can.setFont('Helvetica-Bold', 10)
            # Write student data at precise coordinates (values only, no field names)
            can.drawString(200, 677, leave.student.get_full_name())
            can.drawString(483, 677, leave.student.roll_number)
            # Category of Registration (TA/TAP/RA/FA)
            can.drawString(340, 596, leave.student.category or '')
            can.drawString(250, 657, leave.student.academic_unit or '')
            can.drawString(448, 636, leave.student.academic_programme or '')
            can.drawString(200, 616, leave.student.discipline or '')
            can.drawString(470, 616, leave.student.specialization or '')
            # draw dates as DD MM YYYY (numbers only, no slashes or month names)
            fd = leave.from_date
            td = leave.to_date
            can.drawString(176, 575, fd.strftime('%d     %m    %Y'))
            can.drawString(273, 575, td.strftime('%d     %m    %Y'))
            can.drawString(541, 575, str((leave.to_date - leave.from_date).days + 1))
            # purpose may be long; wrap manually if needed
            text = leave.purpose or ''
            if len(text) > 60:
                # simple wrap: split at 60 chars
                can.drawString(195, 553, text[:60])
                can.drawString(195, 553, text[60:])
            else:
                can.drawString(195, 553, text)
            # place of visit
            can.drawString(200, 533, leave.place_of_visit or '' )
            # ...existing code for faculty advisor and thesis supervisor...
            if leave.faculty_advisor:
                can.drawString(400, 317, f"Faculty Advisor")
            if leave.faculty_advisor:
                can.drawString(110, 290, f" {leave.faculty_advisor}")
            if leave.thesis_supervisor:
                can.drawString(400, 317, f"Thesis Supervisor")
            if leave.thesis_supervisor:
                can.drawString(110, 290, f" {leave.thesis_supervisor}")

            # print submission date on overlay (format: DD Month YYYY)
            try:
                can.drawString(488, 345, leave.submitted_at.strftime('%d     %m      %Y'))
            except Exception:
                # if submitted_at missing for any reason, skip
                pass

            # Draw stipend/scholarship options with tick for selected
            stipend_y_start = 502  # Adjust Y as per your form
            stipend_x = 80        # X coordinate for the box
            stipend_gap = 14       # Vertical gap between options
            stipend_options = [
                ('continue', ''),
                ('not_continue', ''),
                ('not_supported', ''),
            ]
            for idx, (value, label) in enumerate(stipend_options):
                y = stipend_y_start - idx * stipend_gap
                box = '✓' if leave.stipend_status == value else ' '
                can.setFont('Helvetica-Bold', 14)
                can.drawString(stipend_x, y, box)
                can.setFont('Helvetica', 12)
                can.drawString(stipend_x + 25, y, label)

            

            can.save()
            packet.seek(0)
            
            # Read the template PDF
            existing_pdf = PdfReader(template_pdf)
            if existing_pdf.is_encrypted:
                existing_pdf.decrypt('')
            
            # Overlay the new content
            overlay_pdf = PdfReader(packet)
            page = existing_pdf.pages[0]
            page.merge_page(overlay_pdf.pages[0])
            
            # Write output
            output = PdfWriter()
            output.add_page(page)
            
            # Add remaining pages if multi-page
            for i in range(1, len(existing_pdf.pages)):
                output.add_page(existing_pdf.pages[i])
            
            # Save to buffer
            buffer = BytesIO()
            output.write(buffer)
            buffer.seek(0)
            
            filename = f'Leave_Application_{leave.student.roll_number}_{leave.from_date}.pdf'
            return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')
            
        except Exception as e:
            print(f"Error overlaying PDF: {str(e)}")
            # Fall back to generated PDF
            pass
    
    # Fallback: Generate PDF from scratch
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    from datetime import datetime
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=0.3*inch,
        alignment=1
    )
    elements.append(Paragraph('Leave Application Form', title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Student Details Table
    student_data = [
        [f"Application No: {leave.application_number}"],
        [f"Type of Leave: {leave.leave_type.name if leave.leave_type else 'N/A'}"],
        [leave.student.get_full_name()],
        [leave.student.roll_number],
        [leave.student.category or 'N/A'],
        [leave.student.academic_programme or 'N/A'],
        [leave.student.discipline or 'N/A'],
        [leave.student.specialization or 'N/A'],
        [leave.student.academic_unit or 'N/A'],
    ]
    
    student_table = Table(student_data, colWidths=[6*inch])
    student_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(student_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Leave Details
    days = (leave.to_date - leave.from_date).days + 1
    leave_data = [
        [leave.from_date.strftime('%d %m %Y')],
        [leave.to_date.strftime('%d %m %Y')],
        [str(days)],
        [leave.get_status_display()],
        [leave.submitted_at.strftime('%d %m %Y %H:%M')],
    ]
    
    leave_table = Table(leave_data, colWidths=[6*inch])
    leave_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(leave_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Purpose
    elements.append(Paragraph('<b>Purpose of Leave:</b>', styles['Heading3']))
    elements.append(Paragraph(leave.purpose or 'N/A', styles['BodyText']))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph('<b>Place(s) of visit:</b>', styles['Heading3']))
    elements.append(Paragraph(leave.place_of_visit or 'N/A', styles['BodyText']))
    elements.append(Spacer(1, 0.3*inch))
    # Stipend/Scholarship Status (bold, ticked)
    stipend_choices = getattr(leave, 'STIPEND_CHOICES', [
        ('continue', 'My stipend/scholarship from the Institute should be continued during the leave period.'),
        ('not_continue', 'My stipend/scholarship from the Institute need not be continued during the leave period.'),
        ('not_supported', 'I am not supported by a stipend/scholarship from the Institute.'),
    ])
    stipend_selected = leave.stipend_status
    stipend_lines = []
    for value, label in stipend_choices:
        tick = '☑' if value == stipend_selected else '☐'
        stipend_lines.append(f'<b>{tick} {label}</b>')
    elements.append(Paragraph('<b>Stipend/Scholarship Status:</b>', styles['Heading3']))
    for line in stipend_lines:
        elements.append(Paragraph(line, styles['BodyText']))
    elements.append(Spacer(1, 0.2*inch))

    # Faculty Advisor and Thesis Supervisor (only if selected)
    if leave.faculty_advisor:
        elements.append(Paragraph('<b>Faculty Advisor (selected):</b>', styles['Heading3']))
        elements.append(Paragraph(leave.faculty_advisor, styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))
    if leave.thesis_supervisor:
        elements.append(Paragraph('<b>Thesis Supervisor (selected):</b>', styles['Heading3']))
        elements.append(Paragraph(leave.thesis_supervisor, styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))
    elements.append(Spacer(1, 0.2*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1
    )
    elements.append(Paragraph(
        f'Generated on {datetime.now().strftime("%d %m %Y %H:%M:%S")}',
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    filename = f'Leave_Application_{leave.student.roll_number}_{leave.from_date}.pdf'
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')


@login_required
def remove_application(request, pk):
    """Student can cancel their own pending application and regain leave days."""
    leave = get_object_or_404(LeaveApplication, pk=pk, student=request.user)
    if leave.status == 'P':
        leave.delete()
        messages.success(request, 'Application cancelled')
    else:
        messages.error(request, 'Only pending applications can be removed')
    return redirect('core:home')


# ...existing imports...

def is_admin(user):
    return user.is_superuser

def is_admin_or_approver(user):
    return user.is_superuser or user.is_staff

def get_leaves_taken_string(student):
    from core.models import ProgrammeLeavePolicy
    leave_counts = {}
    
    # Initialize all eligible leave types to 0 based on student's programme
    policies = ProgrammeLeavePolicy.objects.filter(
        programme=student.academic_programme,
        is_active=True,
        leave_type__is_active=True
    ).select_related('leave_type')
    
    for policy in policies:
        lt_name = policy.leave_type.name.lower()
        if lt_name == 'maternity leave' and student.gender != 'F':
            continue
        if lt_name == 'paternity leave' and student.gender != 'M':
            continue
        leave_counts[policy.leave_type.name] = 0
        
    approved_apps = student.leaveapplication_set.filter(status='A')
    for app in approved_apps:
        if app.leave_type:
            # Always include leave types that have actual approved applications, even if policy changed
            if app.leave_type.name not in leave_counts:
                leave_counts[app.leave_type.name] = 0
            days = (app.to_date - app.from_date).days + 1
            leave_counts[app.leave_type.name] += days
    
    # Add manual adjustments
    from core.models import StudentLeaveAdjustment
    adjustments = StudentLeaveAdjustment.objects.filter(student=student)
    for adj in adjustments:
        if adj.leave_type.name not in leave_counts:
            leave_counts[adj.leave_type.name] = 0
        leave_counts[adj.leave_type.name] += adj.adjustment_days
    
    parts = []
    for name, count in leave_counts.items():
        short_name = "".join([word[0].upper() for word in name.split() if word.strip()])
        parts.append(f"{short_name}-{count:02d}")
        
    if not parts:
        return "None"
    return ", ".join(parts)


@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    leave_types = LeaveType.objects.filter(is_active=True)
    students = Student.objects.filter(is_superuser=False)
    for student in students:
        student.leaves_taken_formatted = get_leaves_taken_string(student)
        # Prepare list of adjustments for template
        student_adjs = []
        adjustments = {adj.leave_type_id: adj.adjustment_days for adj in StudentLeaveAdjustment.objects.filter(student=student)}
        for lt in leave_types:
            student_adjs.append({
                'id': lt.id,
                'name': lt.name,
                'value': adjustments.get(lt.id, 0)
            })
        student.leave_adjustments = student_adjs
    
    # Removed default total leaves logic
    applications = LeaveApplication.objects.all().order_by('-submitted_at')
    # add duration and leaves_taken_for_type to each application
    for app in applications:
        app.duration = (app.to_date - app.from_date).days + 1
        app.leaves_taken_formatted = get_leaves_taken_string(app.student)
    
    # Get leave types and policies
    leave_types = LeaveType.objects.filter(is_active=True)
    # periodic_leave_types = leave_types.filter(is_periodic=True)
    all_policies = ProgrammeLeavePolicy.objects.select_related('leave_type').order_by('programme')
    
    # Get unique programmes from ProfileForm choices and existing policies
    from django.db.models import Q
    programme_choices = [
        'MTech', 'PhD', 'MTech+PhD', 'MSc+PhD'
    ]
    
    # Auto-backup logic
    backup_config = BackupConfig.load()
    if backup_config.auto_backup_enabled:
        should_backup = False
        if not backup_config.last_backup_at:
            should_backup = True
        else:
            elapsed = timezone.now() - backup_config.last_backup_at
            if elapsed.days >= backup_config.backup_interval_days:
                should_backup = True
        
        if should_backup:
            try:
                os.makedirs('backups', exist_ok=True)
                backup_path = os.path.join('backups', 'backup.json')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    management.call_command('dumpdata', indent=2, stdout=f)
                backup_config.last_backup_at = timezone.now()
                backup_config.save()
            except Exception as e:
                print(f"Auto-backup failed: {str(e)}")

    return render(request, 'core/admin_panel.html', {
        'students': students,
        'applications': applications,
        'leave_types': leave_types,
        'all_policies': all_policies,
        'programme_choices': programme_choices,
        'pending_count': applications.filter(status='P').count(),
        'approved_count': applications.filter(status='A').count(),
        'rejected_count': applications.filter(status='R').count(),
        'approver_config': ApproverConfig.load(),
        'backup_config': BackupConfig.load(),
    })


@login_required
@user_passes_test(is_admin_or_approver)
def approver_panel(request):
    config = ApproverConfig.load()
    applications = LeaveApplication.objects.all().order_by('-submitted_at')
    for app in applications:
        app.duration = (app.to_date - app.from_date).days + 1
        app.leaves_taken_formatted = get_leaves_taken_string(app.student)

    context = {
        'applications': applications,
        'config': config,
        'pending_count': applications.filter(status='P').count(),
        'approved_count': applications.filter(status='A').count(),
        'rejected_count': applications.filter(status='R').count(),
    }

    if config.show_students_tab:
        students = Student.objects.filter(is_superuser=False, is_staff=False)
        for student in students:
            student.leaves_taken_formatted = get_leaves_taken_string(student)
        context['students'] = students

    if config.show_policies_tab:
        context['leave_types'] = LeaveType.objects.filter(is_active=True)
        context['all_policies'] = ProgrammeLeavePolicy.objects.select_related('leave_type').order_by('programme')

    return render(request, 'core/approver_panel.html', context)


@login_required
@user_passes_test(is_admin)
def remove_student(request, pk):
    student = get_object_or_404(Student, pk=pk, is_superuser=False)
    student.delete()
    messages.success(request, 'Student removed')
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
@require_POST
def save_approver_config(request):
    """Save approver panel configuration from admin settings tab."""
    config = ApproverConfig.load()

    bool_fields = [
        'show_students_tab', 'show_policies_tab', 'show_status_cards',
        'show_app_no', 'show_student_name', 'show_roll', 'show_type',
        'show_period', 'show_days', 'show_leaves_taken', 'show_purpose',
        'show_status', 'show_submitted',
        'can_approve', 'can_reject',
        'show_stu_name', 'show_stu_roll', 'show_stu_gender',
        'show_stu_programme', 'show_stu_discipline',
        'show_stu_specialization', 'show_stu_taken',
    ]

    for field in bool_fields:
        setattr(config, field, field in request.POST)

    config.save()
    messages.success(request, 'Approver panel settings saved successfully.')
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
def update_students_from_excel(request):
    """Allow admin to upload a CSV file to update student details."""
    if request.method == 'POST':
        csv_file = request.FILES.get('excel_file')
        if not csv_file:
            messages.error(request, 'No file uploaded')
            return redirect('core:admin_panel')
        
        try:
            result = import_students_from_csv(csv_file)
            skipped = result.skipped_lines

            msg = f'Updated {result.updated} students, created {result.created} new students.'
            messages.success(request, msg)
            if skipped:
                all_lines = ', '.join(str(n) for n in skipped)
                logger.warning(
                    f'Skipped {len(skipped)} malformed row(s) in '
                    f'{csv_file.name!r}: line(s) {all_lines}'
                )
                shown = ', '.join(str(n) for n in skipped[:10])
                more = f' and {len(skipped) - 10} more' if len(skipped) > 10 else ''
                messages.warning(
                    request,
                    f'Skipped {len(skipped)} malformed row(s) with too many '
                    f'columns: line {shown}{more}.'
                )
        except Exception as e:
            logger.exception(f'Failed to import students from file: {csv_file.name}')
            messages.error(request, f'Error processing file: {str(e)}')
        
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
def set_total_leaves(request):
    if request.method == 'POST':
        try:
            new_total = int(request.POST.get('total_leaves', '').strip())
        except ValueError:
            messages.error(request, 'Invalid number for total leaves')
            return redirect('core:admin_panel')
        students = Student.objects.filter(is_superuser=False)
        for s in students:
            diff = new_total - s.total_leaves
            s.leave_balance = max(0, s.leave_balance + diff)
            s.total_leaves = new_total
            s.save()
        messages.success(request, f'Updated total leaves to {new_total}')
    return redirect('core:admin_panel')

    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin_or_approver)
def approve_leave(request, pk):
    # Check if non-admin approver has permission
    if not request.user.is_superuser:
        config = ApproverConfig.load()
        if not config.can_approve:
            messages.error(request, 'You do not have permission to approve applications.')
            return redirect('core:approver_panel')
    leave = get_object_or_404(LeaveApplication, pk=pk)
    if leave.status == 'P':
        days = (leave.to_date - leave.from_date).days + 1
        student = leave.student
        if leave.leave_type:
            policy = ProgrammeLeavePolicy.objects.filter(
                programme=student.academic_programme,
                leave_type=leave.leave_type,
                is_active=True
            ).first()
            _, remaining = get_leave_type_balances(student, leave.leave_type, policy)
            if remaining >= days:
                student.leave_balance = max(0, student.leave_balance - days)
                student.save()
                leave.status = 'A'
                leave.save()
                messages.success(request, 'Leave approved and balance updated')
            else:
                messages.error(request, f'Not enough leave balance for {leave.leave_type.name} to approve')
        else:
            if student.leave_balance >= days:
                student.leave_balance -= days
                student.save()
                leave.status = 'A'
                leave.save()
                messages.success(request, 'Leave approved and balance updated')
            else:
                messages.error(request, 'Not enough leave balance to approve')
    if request.user.is_superuser:
        return redirect('core:admin_panel')
    return redirect('core:approver_panel')


@login_required
@user_passes_test(is_admin_or_approver)
def reject_leave(request, pk):
    # Check if non-admin approver has permission
    if not request.user.is_superuser:
        config = ApproverConfig.load()
        if not config.can_reject:
            messages.error(request, 'You do not have permission to reject applications.')
            return redirect('core:approver_panel')
    leave = get_object_or_404(LeaveApplication, pk=pk)
    if request.method == 'POST' and leave.status == 'P':
        reason = request.POST.get('rejection_reason', '').strip()
        pdf_file = request.FILES.get('rejection_pdf')
        leave.status = 'R'
        leave.rejection_reason = reason
        if pdf_file:
            leave.rejection_pdf = pdf_file
        leave.save()
        messages.success(request, 'Leave rejected with reason.')
    if request.user.is_superuser:
        return redirect('core:admin_panel')
    return redirect('core:approver_panel')


@login_required
@user_passes_test(is_admin)
def create_leave_type(request):
    """Create a new leave type from admin panel."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        color = request.POST.get('color', '#3498db')
        
        if not name:
            messages.error(request, 'Leave type name is required')
            return redirect('core:admin_panel')
        
        if LeaveType.objects.filter(name=name).exists():
            messages.error(request, f'Leave type "{name}" already exists')
            return redirect('core:admin_panel')
        
        LeaveType.objects.create(name=name, description=description, color=color, is_active=True)
        messages.success(request, f'Leave type "{name}" created successfully')
    
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
def create_programme_policy(request):
    """Create a new programme leave policy from admin panel."""
    if request.method == 'POST':
        leave_type_id = request.POST.get('leave_type_id')
        programme = request.POST.get('programme', '').strip()
        days_allowed = request.POST.get('days_allowed', '0')
        
        if not leave_type_id or not programme or not days_allowed:
            messages.error(request, 'All fields are required')
            return redirect('core:admin_panel')
        
        try:
            leave_type = LeaveType.objects.get(id=leave_type_id, is_active=True)
            days_allowed = int(days_allowed)
            
            if days_allowed < 0:
                messages.error(request, 'Days allowed must be >= 0')
                return redirect('core:admin_panel')
            
            policy, created = ProgrammeLeavePolicy.objects.get_or_create(
                programme=programme,
                leave_type=leave_type,
                defaults={'days_allowed': days_allowed, 'is_active': True}
            )
            
            if not created:
                policy.days_allowed = days_allowed
                policy.is_active = True
                policy.save()
                messages.success(request, f'Policy updated: {programme} - {leave_type.name}')
            else:
                messages.success(request, f'Policy created: {programme} - {leave_type.name}')
        
        except LeaveType.DoesNotExist:
            messages.error(request, 'Invalid leave type')
        except ValueError:
            messages.error(request, 'Days allowed must be a number')
    
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
def delete_policy(request, pk):
    """Delete a programme leave policy."""
    policy = get_object_or_404(ProgrammeLeavePolicy, pk=pk)
    leave_type_name = policy.leave_type.name
    programme = policy.programme
    policy.delete()
    messages.success(request, f'Deleted: {programme} - {leave_type_name}')
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
def edit_policy(request, pk):
    """Edit a programme leave policy - update days allowed."""
    policy = get_object_or_404(ProgrammeLeavePolicy, pk=pk)
    
    if request.method == 'POST':
        days_allowed = request.POST.get('days_allowed', '0')
        try:
            days_allowed = int(days_allowed)
            if days_allowed < 0:
                messages.error(request, 'Days allowed must be >= 0')
            else:
                old_days = policy.days_allowed
                policy.days_allowed = days_allowed
                policy.save()
                messages.success(request, f'Updated {policy.programme} - {policy.leave_type.name}: {old_days} → {days_allowed} days')
        except ValueError:
            messages.error(request, 'Days allowed must be a number')
    
    return redirect('core:admin_panel')

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import subprocess

def manual_periodic_leave(request):
    # This function is now disabled because periodic leaves are not supported.
    return HttpResponse(status=405)

from django.views.decorators.csrf import csrf_exempt

def set_periodic_leave_type(request):
    # This function is now disabled because periodic leaves are not supported.
    messages.info(request, 'Periodic leave type settings are not available.')
    return redirect('core:admin_panel')

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            if getattr(user, 'first_login', False):
                user.first_login = False
                user.save(update_fields=['first_login'])
            messages.success(request, 'Your password was successfully updated!')
            
            # Redirect to appropriate dashboard
            if user.is_superuser:
                return redirect('core:admin_panel')
            elif user.is_staff:
                return redirect('core:approver_panel')
            else:
                if not user.academic_unit or not user.academic_programme or not user.discipline:
                    return redirect('core:change_password')
                return redirect('core:home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
        
    return render(request, 'core/change_password.html', {
        'form': form
    })

@login_required
def complete_profile(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect('core:landing')
        
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile completed successfully.')
            return redirect('core:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=request.user)
        
    return render(request, 'core/complete_profile.html', {'form': form})


@login_required
@user_passes_test(is_admin)
@require_POST
def update_student_leave_adjustment(request, pk):
    student = get_object_or_404(Student, pk=pk)
    # Clear existing adjustments for types not in POST? No, just update.
    for key, value in request.POST.items():
        if key.startswith('adj_'):
            try:
                leave_type_id = int(key.replace('adj_', ''))
                adjustment_days = int(value or 0)
                leave_type = get_object_or_404(LeaveType, id=leave_type_id)
                
                adj, created = StudentLeaveAdjustment.objects.get_or_create(
                    student=student,
                    leave_type=leave_type
                )
                adj.adjustment_days = adjustment_days
                adj.save()
            except (ValueError, LeaveType.DoesNotExist):
                continue
                
    messages.success(request, f"Leave adjustments updated for {student.roll_number}")
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
@require_POST
def rollover_year(request):
    config = ApproverConfig.load()
    old_year = config.current_academic_year
    new_year = old_year + 1
    config.current_academic_year = new_year
    config.save()
    messages.success(request, f"Successfully rolled over academic year from July {old_year} to July {new_year}. MTech balances have been renewed to original, and PhD leaves carried forward.")
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
@require_POST
def save_backup_config(request):
    config = BackupConfig.load()
    config.auto_backup_enabled = request.POST.get('auto_backup_enabled') == 'on'
    try:
        config.backup_interval_days = int(request.POST.get('backup_interval_days', 7))
    except ValueError:
        pass
    config.save()
    messages.success(request, "Backup configuration updated.")
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
@require_POST
def manual_backup(request):
    try:
        os.makedirs('backups', exist_ok=True)
        backup_path = os.path.join('backups', 'backup.json')
        with open(backup_path, 'w', encoding='utf-8') as f:
            management.call_command('dumpdata', indent=2, stdout=f)
        
        config = BackupConfig.load()
        config.last_backup_at = timezone.now()
        config.save()
        
        messages.success(request, "Backup created successfully.")
    except Exception as e:
        messages.error(request, f"Error creating backup: {str(e)}")
    return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
def download_backup(request):
    backup_path = os.path.join('backups', 'backup.json')
    if os.path.exists(backup_path):
        return FileResponse(open(backup_path, 'rb'), as_attachment=True, filename='backup.json')
    else:
        messages.error(request, "No backup file found. Please create one first.")
        return redirect('core:admin_panel')


@login_required
@user_passes_test(is_admin)
@require_POST
def restore_backup(request):
    if 'backup_file' not in request.FILES:
        messages.error(request, "No file uploaded.")
        return redirect('core:admin_panel')
    
    backup_file = request.FILES['backup_file']
    if not backup_file.name.endswith('.json'):
        messages.error(request, "Invalid file format. Please upload a .json file.")
        return redirect('core:admin_panel')
    
    try:
        # Save uploaded file temporarily
        os.makedirs('backups', exist_ok=True)
        temp_path = os.path.join('backups', 'restore_temp.json')
        with open(temp_path, 'wb+') as destination:
            for chunk in backup_file.chunks():
                destination.write(chunk)
        
        # Restore data
        # Note: loaddata might fail if ContentTypes or Permissions are in the dump and already exist
        management.call_command('loaddata', temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        messages.success(request, "Database restored successfully.")
    except Exception as e:
        messages.error(request, f"Error restoring database: {str(e)}")
    
    return redirect('core:admin_panel')
