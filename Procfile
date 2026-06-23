web: gunicorn afe.wsgi:application
release: python manage.py migrate && python create_superuser.py