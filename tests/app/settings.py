from django.conf import global_settings
import os


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'tests.app',
    'django_tables2',
]

ROOT_URLCONF = 'tests.app.urls'

SECRET_KEY = "this is super secret"

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request'
] + list(global_settings.TEMPLATE_CONTEXT_PROCESSORS)

TIME_ZONE = "Australia/Brisbane"

USE_TZ = True

if 'SKIP_HAYSTACK' not in os.environ:
    INSTALLED_APPS += [
        'haystack',
    ]
    HAYSTACK_SEARCH_ENGINE = 'simple',
    HAYSTACK_SITECONF = 'tests.app.models'
