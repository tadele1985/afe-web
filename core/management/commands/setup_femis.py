from django.core.management.base import BaseCommand
from core.models import AfeUser, Role, UserRole

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Create roles
        roles = [
            {"name": "System Administrator", "code": "SYSTEM_ADMINISTRATOR"},
            {"name": "Data Administrator", "code": "DATA_ADMINISTRATOR"},
            {"name": "Data Analyst", "code": "DATA_ANALYST"},
            {"name": "Branch User", "code": "BRANCH_USER"},
        ]
        for r in roles:
            Role.objects.get_or_create(code=r["code"], defaults={"name": r["name"]})
            self.stdout.write(f"✅ Role: {r['code']}")

        # Create femis_admin user
        if not AfeUser.objects.filter(username="femis_admin").exists():
            user = AfeUser.objects.create_user(
                username="femis_admin",
                password="Admin@1234",
                first_name="FEMIS",
                last_name="System Admin",
                is_active=True,
            )
            role = Role.objects.get(code="SYSTEM_ADMINISTRATOR")
            UserRole.objects.create(user=user, role=role)
            self.stdout.write("✅ femis_admin created with SYSTEM_ADMINISTRATOR role")
        else:
            self.stdout.write("⚠️  femis_admin already exists")