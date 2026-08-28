# 📋 ADMIN CHECKLIST - Leave Type Configuration

## Pre-Launch Checklist

### ✅ Database Setup
- [ ] Backup current database (`db.sqlite3`)
- [ ] Run: `python manage.py migrate`
- [ ] Verify no migration errors
- [ ] Check Django admin loads without errors

### ✅ Initial Configuration (Choose One Option)

#### Option A: Use Sample Data (Recommended)
- [ ] Run: `python manage.py load_leave_types`
- [ ] Verify 5 leave types created
- [ ] Verify 8 policies created
- [ ] Customize as needed in Admin

#### Option B: Manual Setup
1. **Create Leave Types**
   - [ ] Casual Leave (#3498db) - Active
   - [ ] Maternity Leave (#e74c3c) - Active
   - [ ] Paternity Leave (#f39c12) - Active
   - [ ] Sick Leave (#e67e22) - Active
   - [ ] Research Leave (#27ae60) - Active

2. **Create Policies for Each Programme**
   - [ ] MTech - Casual: 15 days
   - [ ] MTech - Maternity: 90 days
   - [ ] MTech - Paternity: 15 days
   - [ ] MTech - Sick: 5 days
   - [ ] PhD - Casual: 20 days
   - [ ] PhD - Maternity: 90 days
   - [ ] PhD - Research: 30 days
   - (Add more as needed)

---

## Testing Checklist

### 👨‍🎓 Student Testing
- [ ] Login as MTech student
- [ ] Go to "Apply Leave"
- [ ] ✅ See "Type of Leave" dropdown
- [ ] ✅ See only MTech-applicable types (NOT PhD types)
- [ ] Select a type, choose dates, apply
- [ ] ✅ Application saves with leave type
- [ ] ✅ Admin can see leave type on application

- [ ] Login as PhD student
- [ ] Go to "Apply Leave"
- [ ] ✅ See different leave types (matching PhD programme)
- [ ] Apply and verify

### 👨‍💼 Admin Testing
- [ ] Go to Django Admin
- [ ] ✅ "Leave Types" section visible
- [ ] ✅ "Programme Leave Policies" section visible
- [ ] Create new leave type → Works?
- [ ] Create new policy → Works?
- [ ] Filter applications by leave type → Works?

### 🔴 Error Handling
- [ ] Student tries to apply for more days than limit → Shows error?
- [ ] Student tries to apply without selecting type → Shows error?
- [ ] Existing applications still load → Works?
- [ ] Old staff accounts still work → Works?

---

## First Week Operations

### Day 1: Launch
- [ ] Notify students of new feature via email/announcement
- [ ] Post instructions: "Select leave type when applying"
- [ ] Monitor for errors/bugs

### Day 2-3: Monitor
- [ ] Check application submissions
- [ ] Monitor for "Leave type not appearing" reports
- [ ] Verify approvals/rejections working

### Day 4-7: Optimize
- [ ] Gather feedback from admins and students
- [ ] Adjust day allocations if needed
- [ ] Add/disable leave types as needed
- [ ] Document final configuration

---

## Common Tasks

### Task: Add New Leave Type

**Steps:**
1. Go to Django Admin → Leave Types → Add
2. Enter:
   - Name: "Bereavement Leave"
   - Description: "Leave for family bereavement"
   - Color: "#2c3e50" (dark)
   - Is Active: ✓
3. Click Save
4. Go to Programme Leave Policies → Add
5. For each programme:
   - Select Leave Type: "Bereavement Leave"
   - Enter Programme: "MTech" (repeat for each)
   - Days Allowed: 7
   - Is Active: ✓
   - Save

### Task: Adjust Days Allowed

**Steps:**
1. Go to Django Admin → Programme Leave Policies
2. Find: "MTech - Casual Leave"
3. Change "Days Allowed" from 15 to 20
4. Click Save
5. ✅ All future MTech students get 20 days

### Task: Disable a Leave Type

**Steps:**
1. Go to Django Admin → Leave Types
2. Click "Casual Leave"
3. Uncheck "Is Active"
4. Save
5. ✅ Students won't see it when applying

### Task: View All Applications for a Type

**Steps:**
1. Go to Django Admin → Leave Applications
2. Under "Leave Type" filter, select "Maternity Leave"
3. ✅ See only Maternity Leave applications
4. Can approve/reject from here

---

## Admin Dashboard Quick Links

| Task | Link | Keyboard |
|------|------|----------|
| Manage Leave Types | `/admin/core/leavetype/` | Ctrl+K → "Leave Types" |
| Manage Policies | `/admin/core/programmeleavepoliy/` | Ctrl+K → "Policies" |
| View Applications | `/admin/core/leaveapplication/` | Ctrl+K → "Applications" |
| Filter by Type | `/admin/core/leaveapplication/?leave_type__id__exact=1` | Click filter → Leave Type |

---

## Troubleshooting

### ❌ Students don't see leave type dropdown
**Fix:**
1. Check: Is policy created for their programme?
2. Check: Is leave type marked "Is Active: ✓"?
3. Check: Does policy have "Is Active: ✓"?
4. Check: Is programme name exactly matching?

### ❌ Migration failed
**Fix:**
1. Backup database
2. Check database permissions
3. Run: `python manage.py migrate core`
4. If still fails, roll back or restore backup

### ❌ Old applications show no leave type
**Fix:** This is normal! They're backward compatible. You can:
- Edit application and add leave type manually
- Or leave them as-is (they still work)

### ❌ Students can apply for more days than allowed
**Fix:**
1. Check policy "Days Allowed" value
2. Verify policy "Is Active: ✓"
3. Verify student's programme matches policy
4. Restart Django server if changes don't reflect

---

## Configuration Template

### For Your Institution
Copy and customize:

```
LEAVE TYPES FOR [YOUR INSTITUTION]:

[ ] Casual Leave - General purpose
    - MTech: ___ days
    - PhD: ___ days

[ ] Maternity Leave - Female students
    - MTech: ___ days
    - PhD: ___ days

[ ] Paternity Leave - Male students
    - MTech: ___ days
    - PhD: ___ days

[ ] Sick Leave - Medical
    - MTech: ___ days
    - PhD: ___ days

[ ] _____________ - _________________
    - MTech: ___ days
    - PhD: ___ days

[ ] _____________ - _________________
    - MTech: ___ days
    - PhD: ___ days
```

---

## Support & Documentation

- **Quick Setup**: See `QUICK_START_LEAVE_TYPES.md`
- **Detailed Guide**: See `LEAVE_TYPE_SETUP.md`
- **Technical Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Code Changes**: See comments in `core/models.py`, `core/admin.py`, `core/views.py`

---

## Feedback & Improvements

**Track Issues:**
- Document any bugs/unexpected behavior
- Note feature requests from users
- Plan improvements for next iteration

**Email for Support:**
- If Django admin not loading
- If migrations fail
- If leave types not appearing for students

---

**Last Updated**: April 27, 2026  
**Feature Status**: ✅ Ready for Deployment  
**Support Level**: Production-Ready
