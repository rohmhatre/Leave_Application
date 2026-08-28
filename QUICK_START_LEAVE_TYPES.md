# 🎯 QUICK START - Leave Type Feature

## What Was Implemented?

A complete system for admins to manage **different types of leaves** (Casual, Maternity, Paternity, Sick, etc.) with **different allocations per programme** (MTech, PhD, etc.).

## 📋 Step-by-Step Setup

### 1️⃣ **Run Migration**
```bash
python manage.py migrate
```
This creates the new database tables for `LeaveType` and `ProgrammeLeavePolicy`.

### 2️⃣ **Load Sample Data (Optional)**
```bash
python manage.py load_leave_types
```
This loads 5 pre-configured leave types with policies for MTech and PhD programmes.

**Or manually via Django Admin:**

### 3️⃣ **Create Leave Types** (Admin Dashboard)
1. Go to `/admin/`
2. Click **Leave Types** (under "CORE")
3. Click **Add Leave Type**
4. Fill in:
   - **Name**: "Casual Leave"
   - **Description**: "Regular casual leave"
   - **Color**: "#3498db"
   - **Is Active**: ✓
5. Click **Save**

Repeat for:
- Maternity Leave
- Paternity Leave
- Sick Leave
- Research Leave

### 4️⃣ **Create Programme Policies** (Admin Dashboard)
Method A - **From Leave Type**:
1. Go to Leave Type → Click **"Casual Leave"**
2. Scroll to "Programme Leave Policies" section
3. Click **Add another Programme Leave Poliy**
4. Fill:
   - **Programme**: "MTech"
   - **Days Allowed**: 15
   - **Is Active**: ✓
5. Click **Save**

Method B - **From Programme Policies**:
1. Go to **Programme Leave Policies** (under CORE)
2. Click **Add Programme Leave Policy**
3. Fill all fields and save

### 5️⃣ **Test the Feature**
1. Login as a **student**
2. Go to **"Apply Leave"** page
3. ✅ New **"Type of Leave"** dropdown should appear
4. Select a leave type → Choose dates → Apply

---

## 📊 Database Schema

### LeaveType Table
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary Key |
| name | String(100) | Unique (e.g., "Casual Leave") |
| description | Text | Optional |
| color | String(7) | Hex color for UI |
| is_active | Boolean | Enable/disable |
| created_at | DateTime | Auto-filled |

### ProgrammeLeavePolicy Table
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary Key |
| programme | String(100) | e.g., "MTech", "PhD" |
| leave_type | FK | Links to LeaveType |
| days_allowed | Integer | Max days for this type in this programme |
| is_active | Boolean | Enable/disable |
| created_at | DateTime | Auto-filled |
| updated_at | DateTime | Auto-updated |

### Updated LeaveApplication Table
| New Field | Type | Notes |
|-----------|------|-------|
| leave_type | FK | Links to LeaveType (Nullable for backward compatibility) |

---

## 🎨 Admin Interface

### Leave Types Admin
- **View/Edit** all leave types
- **Add inline policies** for different programmes
- **Toggle active/inactive** status
- **Color coding** for UI display

### Programme Leave Policies Admin
- **Manage** leave allocations per programme
- **Filter** by programme or leave type
- **Batch update** multiple policies

### Leave Applications Admin (Enhanced)
- **Filter** by leave type
- **See** which leave type each application used
- **Better organization** with fieldsets

---

## ✨ Key Features

✅ **Programme-Specific Policies**: MTech gets 15 Casual days, PhD gets 20 days  
✅ **Multiple Leave Types**: Support for any number of leave types  
✅ **Validation**: System checks against both total balance AND leave-type limit  
✅ **Easy Admin Interface**: Intuitive Django admin  
✅ **Color Coding**: Visual distinction between leave types  
✅ **Backward Compatible**: Old leave applications still work  

---

## 📝 Admin Reference

### Create Casual Leave with 15 days for MTech
1. **Leave Types** → Add
   - Name: "Casual Leave"
   - Description: "Regular casual leave"
   - Color: "#3498db"
   - Is Active: ✓
   
2. **Programme Leave Policies** → Add
   - Programme: "MTech"
   - Leave Type: "Casual Leave"
   - Days Allowed: 15
   - Is Active: ✓

### Create Maternity Leave with 90 days for all programmes
1. **Leave Types** → Add
   - Name: "Maternity Leave"
   - Color: "#e74c3c"
   
2. **Programme Leave Policies** → Add (repeat for each programme)
   - Programme: "MTech", Days: 90
   - Programme: "PhD", Days: 90
   - Programme: "MSc+PhD", Days: 90

---

## 🔧 Advanced

### Filter Leave Applications by Type
```
Django Admin → Leave Applications → Leave Type (filter)
```

### Get Leave Type Allocations for a Student
```python
from core.models import ProgrammeLeavePolicy

# Get all policies for a student's programme
policies = ProgrammeLeavePolicy.objects.filter(
    programme=student.academic_programme,
    is_active=True
)

for policy in policies:
    print(f"{policy.leave_type.name}: {policy.days_allowed} days")
```

### Display in Templates
```html
{{ leave.leave_type.name }}
{% if leave.leave_type %}
  <span style="color: {{ leave.leave_type.color }}">{{ leave.leave_type.name }}</span>
{% endif %}
```

---

## ⚠️ Important Notes

1. **Migration**: Must run `migrate` before the feature works
2. **Leave Type Required**: Students must select a leave type when applying
3. **Validation**: System checks against leave-type daily limits
4. **Backwards Compatibility**: Existing applications with null leave_type still work
5. **Admin Only**: Only admins can create/edit leave types and policies

---

## 🚀 Next Steps

1. ✅ Run `python manage.py migrate`
2. ✅ Create leave types in Admin
3. ✅ Create programme policies
4. ✅ Test with a student account
5. ✅ Customize colours as needed

---

**Need Help?** Check `LEAVE_TYPE_SETUP.md` for detailed documentation.
