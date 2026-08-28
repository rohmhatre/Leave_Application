# Leave Type Management Feature - Setup Guide

## Overview
This feature allows admins to create different types of leaves (Casual, Maternity, Paternity, Sick, etc.) and define specific leave allocations for each programme (MTech, PhD, etc.).

## Changes Made

### 1. **New Models**
- **LeaveType**: Defines types of leaves available in the system
  - `name`: Name of the leave type (e.g., "Casual Leave", "Maternity Leave")
  - `description`: Optional description
  - `color`: Hex color code for UI display
  - `is_active`: To enable/disable leave types

- **ProgrammeLeavePolicy**: Associates leave types with programmes and their allocations
  - `programme`: Academic programme (MTech, PhD, etc.)
  - `leave_type`: FK to LeaveType
  - `days_allowed`: Maximum days allowed for this leave type in this programme
  - `is_active`: Enable/disable the policy

### 2. **Updated LeaveApplication Model**
- Added `leave_type` field (ForeignKey to LeaveType)
- Students now select which type of leave they're applying for

### 3. **Admin Interface Enhancements**

#### LeaveType Management
- Access via Django Admin → **Leave Types**
- Create/edit leave types with name, description, and color
- Mark as active/inactive

#### Programme Leave Policy Management
- **Two ways to manage**:
  1. **From LeaveType**: Open a LeaveType and add policies inline for different programmes
  2. **Direct Admin**: Access via Django Admin → **Programme Leave Policies**
- Define how many days each leave type allows per programme

#### LeaveApplication Admin
- Now shows leave_type in the list view
- Filter applications by leave type
- Better organization with fieldsets

### 4. **Form & View Updates**
- `LeaveForm` now includes leave_type field
- Leave types are auto-filtered based on student's programme
- Validation ensures requested days don't exceed the leave type limit

## Setup Instructions

### Step 1: Run Migration
```bash
python manage.py migrate
```

### Step 2: Create Leave Types
1. Go to Django Admin (`/admin/`)
2. Navigate to **Leave Types**
3. Click **Add Leave Type**
4. Enter details:
   - Name: "Casual Leave"
   - Description: "Regular casual leaves"
   - Color: "#3498db" (optional)
   - Is Active: ✓
5. Repeat for other leave types (Maternity, Paternity, Sick, etc.)

### Step 3: Create Programme-Leave Policies
1. **Option A - From LeaveType Admin**:
   - Go to **Leave Types**
   - Click on a leave type
   - In the "Programme Leave Policies" section, add a row for each programme
   - Fill: Programme (MTech, PhD, etc.), Days Allowed (e.g., 15)
   - Save

2. **Option B - Direct Admin**:
   - Go to **Programme Leave Policies**
   - Click **Add Programme Leave Policy**
   - Select Leave Type, Enter Programme, Set Days Allowed
   - Save

### Step 4: Test the Feature
1. Login as a student
2. Go to **Apply Leave**
3. A **"Type of Leave"** dropdown should appear with available leave types for their programme
4. Select a type and submit
5. Admin can view applications filtered by leave type

## Features

✅ **Programme-Specific Leaves**: Different programmes can have different leave allocations  
✅ **Multiple Leave Types**: Support for Casual, Maternity, Sick, Paternity, etc.  
✅ **Leave Balance Validation**: System validates against both total balance and leave-type limits  
✅ **Easy Admin Management**: Intuitive Django admin interface  
✅ **Color Coding**: Each leave type can have a custom color for UI display  
✅ **Backward Compatibility**: Existing students can still apply with null leave_type  

## Example Setup

### Sample Leave Types
| Leave Type | Description | Color |
|-----------|-------------|-------|
| Casual Leave | Regular casual leaves | #3498db |
| Maternity Leave | Maternity leave for female students | #e74c3c |
| Paternity Leave | Paternity leave for male students | #f39c12 |
| Sick Leave | Medical/illness related leave | #e67e22 |
| Research Leave | For research activities | #27ae60 |

### Sample Programme Policies
| Programme | Leave Type | Days Allowed |
|-----------|-----------|--------------|
| MTech | Casual Leave | 15 |
| MTech | Maternity Leave | 90 |
| PhD | Casual Leave | 20 |
| PhD | Research Leave | 30 |

## API/View Changes

### LeaveForm Initialization
```python
# Pass student object for programme-based filtering
form = LeaveForm(student=request.user)
```

### Adding Leave
```python
leave = LeaveApplication(
    student=user,
    leave_type=selected_type,  # New field
    from_date=from_date,
    to_date=to_date,
    purpose=purpose,
    place_of_visit=place_of_visit
)
leave.save()
```

## Template Updates (if needed)

If you have custom templates beyond the default, update them to display leave_type:
```html
{{ leave.leave_type.name }}  <!-- Display leave type name -->
{{ leave.leave_type.get_color_display }}  <!-- If storing color -->
```

## Future Enhancements

- Add leave type to student dashboard analytics
- Email notifications specifying leave type
- Leave balance tracking per leave type
- Automated balance deduction logic per type
- Leave type approval workflows (some types requiring special approval)

---

**Note**: If you modify the models, remember to:
```bash
python manage.py makemigrations
python manage.py migrate
```
