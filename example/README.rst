The example project only supports the latest version of Django. To get it up and running:

    pip install -r requirements.pip
    python manage.py migrate
    python manage.py loaddata app/fixtures/initial_data.json
    python manage.py runserver
