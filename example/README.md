# Django-tables2 example project

## To get it up and running

```bash
git clone https://github.com/jieter/django-tables2.git

cd django-tables2/example
uv sync

uv run python manage.py migrate
uv run python manage.py loaddata "app/fixtures/initial_data.json"
uv run python manage.py runserver
```

Server should be live at <http://127.0.0.1:8000/> now.
