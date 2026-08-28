from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('logout/', views.student_logout, name='logout'),
    path('apply/', views.apply_leave, name='apply_leave'),
    path('application/<int:pk>/', views.view_application, name='view_application'),
    path('application/<int:pk>/pdf/', views.download_application_pdf, name='download_pdf'),
    path('application/remove/<int:pk>/', views.remove_application, name='remove_application'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('approver-panel/', views.approver_panel, name='approver_panel'),
    path('remove-student/<int:pk>/', views.remove_student, name='remove_student'),
    path('update-students/', views.update_students_from_excel, name='update_students'),
    path('set-total-leaves/', views.set_total_leaves, name='set_total_leaves'),
    path('leave/approve/<int:pk>/', views.approve_leave, name='approve_leave'),
    path('leave/reject/<int:pk>/', views.reject_leave, name='reject_leave'),
    path('leave-type/create/', views.create_leave_type, name='create_leave_type'),
    path('leave-type/delete/<int:pk>/', views.delete_leave_type, name='delete_leave_type'),
    path('policy/create/', views.create_programme_policy, name='create_programme_policy'),
    path('policy/edit/<int:pk>/', views.edit_policy, name='edit_policy'),
    path('policy/delete/<int:pk>/', views.delete_policy, name='delete_policy'),
    path('policy/reset/<int:pk>/', views.reset_policy, name='reset_policy'),
    path('change-password/', views.change_password, name='change_password'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('approver-config/', views.save_approver_config, name='save_approver_config'),
    path('student/adjust-leave/<int:pk>/', views.update_student_leave_adjustment, name='update_student_leave_adjustment'),
    path('backup/save-config/', views.save_backup_config, name='save_backup_config'),
    path('backup/manual/', views.manual_backup, name='manual_backup'),
    path('backup/download/', views.download_backup, name='download_backup'),
    path('backup/restore/', views.restore_backup, name='restore_backup'),
    path('rollover-year/', views.rollover_year, name='rollover_year'),
]