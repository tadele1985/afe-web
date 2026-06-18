#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py loaddata femis_data.json
python manage.py shell -c "
from core.models import AfeUser
print('Total users:', AfeUser.objects.count())
try:
    user = AfeUser.objects.get(username='femis_admin')
    print('User found:', user.username)
    print('Is active:', user.is_active)
    user.set_password('Admin@1234!')
    user.save()
    print('Password reset successfully')
except AfeUser.DoesNotExist:
    print('ERROR: femis_admin user NOT found in database!')
"