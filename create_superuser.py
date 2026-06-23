import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "afe.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "femis_admin"
password = "Admin@1234"
email = "admin@femis.com"

try:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"Superuser created: {user.username}")
    else:
        # Force reset the password in case it was wrong
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        print(f"Superuser password reset: {user.username}")
except Exception as e:
    print(f"Error: {e}")