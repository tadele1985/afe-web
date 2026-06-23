import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "afe.settings")
django.setup()

from django.contrib.auth import get_user_model
from core.models import Role, UserRole, RoleCode

User = get_user_model()

username = "femis_admin"
password = "Admin@1234"
email = "admin@femis.com"

print("=== Starting superuser setup ===")
print(f"Total users in DB: {User.objects.count()}")

try:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✓ Superuser created: {user.username}")
    else:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        print(f"✓ Superuser updated: {user.username}")

    # Assign System Administrator role
    role, created = Role.objects.get_or_create(
        code=RoleCode.SYSTEM_ADMINISTRATOR,
        defaults={"name": "System Administrator"}
    )
    print(f"✓ Role: {role.name} ({'created' if created else 'exists'})")

    user_role, created = UserRole.objects.get_or_create(
        user=user,
        defaults={"role": role}
    )
    print(f"✓ UserRole: {'created' if created else 'already exists'}")
    print("=== Setup complete ===")

except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()