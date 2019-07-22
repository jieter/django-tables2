DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = [
    "tests.app",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_tables2",
]

ROOT_URLCONF = "tests.app.urls"

SECRET_KEY = "this is super secret"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

TIME_ZONE = "Europe/Amsterdam"

SHORT_DATE_FORMAT = "Y-m-d"
TIME_FORMAT = "H:i:s"
SHORT_DATETIME_FORMAT = "Y-m-d H:i:s"

USE_TZ = True
