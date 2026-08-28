from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Student, LeaveApplication, LeaveType, ProgrammeLeavePolicy


class StudentAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('roll_number', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'gender', 'email')}),
        ('Academic info', {'fields': ('academic_unit','academic_programme','discipline','first_login')}),
        ('Permissions', {'fields': ('is_active','is_staff','is_superuser','groups','user_permissions')}),
        ('Important dates', {'fields': ('last_login','date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('roll_number','password1','password2'),
        }),
    )
    list_display = ('roll_number','first_name','last_name','gender','is_staff')
    search_fields = ('roll_number','first_name','last_name')
    ordering = ('roll_number',)


class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'leave_type', 'from_date', 'to_date', 'status', 'submitted_at')
    list_filter = ('status', 'leave_type', 'submitted_at')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name')
    readonly_fields = ('submitted_at',)
    fieldsets = (
        ('Student & Leave Info', {
            'fields': ('student', 'leave_type', 'from_date', 'to_date')
        }),
        ('Details', {
            'fields': ('purpose', 'place_of_visit')
        }),
        ('Status', {
            'fields': ('status', 'submitted_at')
        }),
    )


class ProgrammeLeavePolicyInline(admin.TabularInline):
    model = ProgrammeLeavePolicy
    extra = 1
    fields = ('programme', 'days_allowed', 'is_active')


class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description')
        }),
        ('Display', {
            'fields': ('color',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    inlines = [ProgrammeLeavePolicyInline]


admin.site.register(Student, StudentAdmin)
admin.site.register(LeaveApplication, LeaveApplicationAdmin)
admin.site.register(LeaveType, LeaveTypeAdmin)
