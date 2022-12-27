# Django-tables2 example project

This example project only supports the latest version of Django.

# To get it up and running:

```
git clone https://github.com/jieter/django-tables2.git

cd django-tables2/example
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata app/fixtures/initial_data.json
python manage.py runserver
```

Server should be live at http://127.0.0.1:8000/ now.
