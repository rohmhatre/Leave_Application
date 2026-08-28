import os

path = "./core/views.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace complete_profile redirect with change_password redirect
content = content.replace("redirect('core:complete_profile')", "redirect('core:change_password')")

# For the change_password function, we need to unset first_login
old_code = """        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Your password was successfully updated!')"""

new_code = """        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            if getattr(user, 'first_login', False):
                user.first_login = False
                user.save(update_fields=['first_login'])
            messages.success(request, 'Your password was successfully updated!')"""

content = content.replace(old_code, new_code)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
