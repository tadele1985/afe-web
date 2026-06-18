#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py loaddata femis_data.json
python manage.py shell -c "
from core.models import AfeUser
user = AfeUser.objects.get(username='femis_admin')
user.set_password('Admin@123')
user.save()
print('Password reset done')
"