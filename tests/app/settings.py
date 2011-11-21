from django.conf import global_settings


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'tests.app',
    'django_tables2',
    'haystack',
]


ROOT_URLCONF = 'tests.app.urls'


TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request'
] + list(global_settings.TEMPLATE_CONTEXT_PROCESSORS)


HAYSTACK_SEARCH_ENGINE = 'simple',
HAYSTACK_SITECONF = 'tests.app.models'
