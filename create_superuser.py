import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "afe.settings")
django.setup()

from django.contrib.auth import get_user_model
from core.models import Role, UserRole, RoleCode

User = get_user_model()

print("=== Starting user setup ===")

users_to_create = [
    {
        "username": "femis_admin",
        "password": "Admin@1234",
        "email": "admin@femis.com",
        "role_code": RoleCode.SYSTEM_ADMINISTRATOR,
        "role_name": "System Administrator",
        "is_superuser": True,
        "is_staff": True,
    },
    {
        "username": "data_admin",
        "password": "Admin@1234",
        "email": "dataadmin@femis.com",
        "role_code": RoleCode.DATA_ADMINISTRATOR,
        "role_name": "Data Administrator",
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "username": "branch_user",
        "password": "Admin@1234",
        "email": "branchuser@femis.com",
        "role_code": RoleCode.BRANCH_USER,
        "role_name": "Branch user",
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "username": "data_analyst",
        "password": "Admin@1234",
        "email": "dataanalyst@femis.com",
        "role_code": RoleCode.DATA_ANALYST,
        "role_name": "Data Analyst",
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "username": "branch_data_admin",
        "password": "Admin@1234",
        "email": "branchdataadmin@femis.com",
        "role_code": RoleCode.BRANCH_DATA_ADMINISTRATOR,
        "role_name": "Branch Data Administrator",
        "is_superuser": False,
        "is_staff": False,
    },
    {
        "username": "branch_data_analyst",
        "password": "Admin@1234",
        "email": "branchdataanalyst@femis.com",
        "role_code": RoleCode.BRANCH_DATA_ANALYST,
        "role_name": "Branch Data Analyst",
        "is_superuser": False,
        "is_staff": False,
    },
]

for u in users_to_create:
    try:
        if not User.objects.filter(username=u["username"]).exists():
            if u["is_superuser"]:
                user = User.objects.create_superuser(
                    username=u["username"],
                    email=u["email"],
                    password=u["password"],
                )
            else:
                user = User.objects.create_user(
                    username=u["username"],
                    email=u["email"],
                    password=u["password"],
                )
            print(f"✓ Created user: {u['username']}")
        else:
            user = User.objects.get(username=u["username"])
            user.set_password(u["password"])
            user.is_superuser = u["is_superuser"]
            user.is_staff = u["is_staff"]
            user.is_active = True
            user.save()
            print(f"✓ Updated user: {u['username']}")

        # Create role if not exists
        role, _ = Role.objects.get_or_create(
            code=u["role_code"],
            defaults={"name": u["role_name"]}
        )

        # Assign role to user
        UserRole.objects.get_or_create(
            user=user,
            defaults={"role": role}
        )
        print(f"  → Role assigned: {u['role_name']}")

    except Exception as e:
        print(f"✗ Error creating {u['username']}: {e}")

print(f"\nTotal users in DB: {User.objects.count()}")
print("=== Setup complete ===")