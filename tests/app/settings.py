import os

import six
from django import VERSION
from django.conf import global_settings

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
]

ROOT_URLCONF = 'tests.app.urls'

SECRET_KEY = "this is super secret"

if VERSION < (1, 8):
    TEMPLATE_CONTEXT_PROCESSORS = [
        'django.core.context_processors.request'
    ] + list(global_settings.TEMPLATE_CONTEXT_PROCESSORS)
else:
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

if not six.PY3:  # Haystack isn't compatible with Python 3
    INSTALLED_APPS += [
        'haystack',
    ]
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        }
    }
