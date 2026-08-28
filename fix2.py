import os

path = "./core/views.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update landing
old_landing = """            if user.first_login:
                return redirect('core:change_password')
            return redirect('core:home')"""

new_landing = """            if user.first_login:
                return redirect('core:change_password')
            if not user.academic_unit or not user.academic_programme or not user.discipline:
                return redirect('core:complete_profile')
            return redirect('core:home')"""

content = content.replace(old_landing, new_landing)

# 2. Update home
old_home = """    user = request.user
    if user.first_login:
        return redirect('core:change_password')
    # include this"""

new_home = """    user = request.user
    if user.first_login:
        return redirect('core:change_password')
    if not user.academic_unit or not user.academic_programme or not user.discipline:
        return redirect('core:complete_profile')
    # include this"""

content = content.replace(old_home, new_home)

# 3. Update change_password
old_change_pwd = """            # Redirect to appropriate dashboard
            if user.is_superuser:
                return redirect('core:admin_panel')
            elif user.is_staff:
                return redirect('core:approver_panel')
            else:
                return redirect('core:home')"""

new_change_pwd = """            # Redirect to appropriate dashboard
            if user.is_superuser:
                return redirect('core:admin_panel')
            elif user.is_staff:
                return redirect('core:approver_panel')
            else:
                if not user.academic_unit or not user.academic_programme or not user.discipline:
                    return redirect('core:complete_profile')
                return redirect('core:home')"""

content = content.replace(old_change_pwd, new_change_pwd)

# 4. Add complete_profile view at the end
new_view = """
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
"""

if "def complete_profile" not in content:
    content += new_view

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
