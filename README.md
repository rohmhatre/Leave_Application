# Leave Application Django Website

A comprehensive Django-based leave management portal with student and admin interfaces for managing leave requests, approvals, and balances.

---

## 📋 Features

### Student Features
- **User Authentication**: Roll number & password-based login with first-login password change
- **Profile Completion**: Students complete profile with programme, discipline, and specialization on first login
- **Leave Application**: Submit leave requests with date range and purpose
- **Application Tracking**: View all submitted applications with real-time status (Pending/Approved/Rejected)
- **Leave Balance Display**: See available leaves and track usage
- **Application Management**: Cancel pending applications and regain balance
- **Dashboard**: Student home with application history and quick access to apply

### Admin Features
- **Student Management**: View, update, and remove student records from the database
- **Excel Import**: Bulk import students from Excel with auto-deduplication
- **Leave Application Review**: View all pending applications with student details and duration
- **Approval/Rejection Workflow**: Approve or reject applications with automatic balance deduction
- **Leave Policy Control**: Set default total leave allotment for all students globally
- **Analytics**: View taken leaves and pending applications per student
- **Tabbed Interface**: Organized Students and Leave Applications sections

---

## 🛠 Setup & Installation

### 1. Install Requirements
```bash
pip install django pandas openpyxl reportlab
```

### 2. Run Migrations
```bash
python manage.py migrate
```

> ⚠️ **Important**: If you modify models (e.g., add new fields) or pull updates, run:
> ```bash
> python manage.py makemigrations
> python manage.py migrate
> ```
> This keeps your database schema in sync with the code.

### 3. Create Initial Admin User
Create a admin superuser using the command

```bash
python manage.py createsuperuser
```

Follow the prompts for a succesful setup.

### 4. Import Students from Excel
Prepare an Excel file with columns: `NAME` and `Roll Number`

```bash
python manage.py import_students path/to/students.xlsx
```

Each student will have:
- **Initial Password**: Equal to their roll number
- **Leave Balance**: 15 days (default, customizable from admin panel)

> **Note**: Re-running the import only adds new students; existing records remain unchanged.

### 5. Run Development Server
```bash
python manage.py runserver
```

Open: `http://localhost:8000/`

---

## 📖 Usage Guide

### Landing Page
- **Student Login**: Enter roll number and password
- **Admin Login**: User ID: `ADMIN`, Password: `25m0005@iitb`

### Student Workflow
1. **First Login**: Change password (required)
2. **Profile Completion**: Select/enter programme, discipline, specialization, and academic unit
3. **Home Dashboard**: View leave balance and applications
4. **Apply for Leave**: Submit application with dates and purpose
5. **View Application**: Check status after submission (Pending → Approved/Rejected)

### Admin Workflow
1. **Student Management Tab**:
   - View all students with their details
   - See leaves taken (approved days only)
   - Import/update students from Excel
   - Remove students from system

2. **Leave Applications Tab**:
   - List all applications with:
     - Student details
     - Leave period and days requested
     - Current status (Pending/Approved/Rejected)
   - Approve or reject pending applications
   - Balance automatically updates on approval

3. **Global Settings**:
   - Adjust default leave allotment (e.g., 15 → 20 days)
   - All students' totals and balances adjust proportionally

---

## 🔑 Key Concepts

### Leave Balance System
- **Initial Balance**: 15 days per student (configurable)
- **Balance Deduction**: Occurs **only on approval**, not on submission
- **Pending Applications**: Do NOT affect available balance
- **Rejection**: Doesn't alter balance (never deducted)
- **Cancellation**: Students can cancel pending applications anytime

### Application Status Badges
- 🟡 **Pending**: Awaiting admin review
- 🟢 **Approved**: Leaves deducted, request confirmed
- 🔴 **Rejected**: Application denied, balance unchanged

### Admin Panel Columns (Student List)
| Column | Description |
|--------|-------------|
| Name | Full name |
| Roll | Roll number/ID |
| Programme | MTech, PhD, MSc+PhD, etc. |
| Discipline | Aerospace Engineering, etc. |
| Specialization | Aerodynamics, Propulsion, etc. |
| Taken | Total approved leaves used |
| Action | Remove button |

### Leave Applications Table
| Column | Description |
|--------|-------------|
| Student | Name of applicant |
| Roll | Student roll number |
| Period | From and to dates |
| Days | Number of days requested |
| Purpose | Reason for leave |
| Status | Current application state |
| Submitted | Timestamp of submission |
| Action | Approve/Reject buttons (if pending) |

---

## 📁 Project Structure

```
Leave_Application/
├── manage.py
├── db.sqlite3
├── leave_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── models.py                 # Student, LeaveApplication models
│   ├── views.py                  # All view logic
│   ├── urls.py                   # URL routing
│   ├── forms.py                  # ProfileForm, LeaveForm
│   ├── management/commands/
│   │   └── import_students.py    # Excel import command
│   └── templates/core/
│       ├── landing.html          # Login page
│       ├── home.html             # Student dashboard
│       ├── apply_leave.html      # Application form
│       ├── view_application.html # Application details
│       ├── complete_profile.html # Profile form
│       ├── admin_panel.html      # Admin interface
│       └── change_password.html  # Password change
└── README.md
```

---

## 🔐 Security Notes

- Passwords are hashed using Django's default PBKDF2 algorithm
- Custom `Student` model (AbstractUser) replaces Django's default User
- CSRF tokens on all forms
- Login required decorators on protected views
- Admin-only views protected with `@user_passes_test(is_admin)`

---

## 🎨 Technology Stack

- **Backend**: Django 6.0.1
- **Database**: SQLite
- **Frontend Styling**: Bootstrap 5.3.2
- **Data Import**: Pandas, openpyxl
- **PDF Export**: ReportLab (optional)

---

## 📝 Model Fields

### Student
- `roll_number` (unique identifier)
- `first_name`, `last_name`
- `academic_unit` (Aerospace Department)
- `academic_programme` (MTech, PhD, etc.)
- `discipline` (Aerospace Engineering, etc.)
- `specialization` (Aerodynamics, Propulsion, etc.)
- `total_leaves` (default: 15)
- `leave_balance` (deducted on approval)
- `first_login` (password change flag)

### LeaveApplication
- `student` (ForeignKey)
- `from_date`, `to_date`
- `purpose` (text field)
- `status` (P=Pending, A=Approved, R=Rejected)
- `submitted_at` (auto timestamp)

---

## 🚀 Common Tasks

### Reset a Student's Leave Balance
```bash
python manage.py shell
from core.models import Student
s = Student.objects.get(roll_number='25m0005')
s.leave_balance = 15
s.save()
```

### Delete All Pending Applications (Admin Only)
```bash
python manage.py shell
from core.models import LeaveApplication
LeaveApplication.objects.filter(status='P').delete()
```

### Export Approved Leaves (Python Script)
```python
from core.models import LeaveApplication
import csv

apps = LeaveApplication.objects.filter(status='A')
with open('approved_leaves.csv', 'w') as f:
    writer = csv.writer(f)
    for app in apps:
        writer.writerow([app.student.roll_number, app.from_date, app.to_date])
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "no such column: core_student.leave_balance" | Run `makemigrations && migrate` |
| Admin user not created | Delete db.sqlite3 and migrate again |
| Students can't log in | Ensure `username` field is set (import command handles this) |
| Excel import fails | Verify columns are named exactly: `NAME`, `Roll Number` |
| Template syntax errors | Ensure spaces around `==` in if statements (e.g., `{% if app.status == 'P' %}`) |

---

## 📞 Support & Customization

- **Add PDF generation**: Use ReportLab to export applications as PDFs
- **Email notifications**: Integrate Django's email backend for approval/rejection alerts
- **Advanced reporting**: Add leave analytics dashboard
- **Multi-department support**: Extend Academic Unit to support multiple departments
- **Approval hierarchy**: Implement multi-level approvals (HOD → Director)

---

## 📄 License

This project is provided as-is for educational and institutional use.

---

## ✨ Future Enhancements

- [ ] PDF export of leave applications
- [ ] Email notifications on status changes
- [ ] Leave type categorization (Sick, Casual, etc.)
- [ ] Holiday calendar integration
- [ ] Mobile-friendly responsive design improvements
- [ ] API endpoints for integration
- [ ] Advanced search and filtering
- [ ] Leave carryover policies

---

Enjoy using the Leave Application Portal! 🎉

