DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'tests.app',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_tables2',
    'haystack',
]

ROOT_URLCONF = 'tests.app.urls'

SECRET_KEY = "this is super secret"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request'
            ],
        }
    }
]

TIME_ZONE = "Australia/Brisbane"

USE_TZ = True

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    }
}
