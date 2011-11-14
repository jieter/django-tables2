from django.conf import global_settings


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'tests.testapp',
    'django_tables2',
    'haystack',
]


ROOT_URLCONF = 'tests.testapp.urls'


TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request'
] + list(global_settings.TEMPLATE_CONTEXT_PROCESSORS)


HAYSTACK_SEARCH_ENGINE = 'simple',
HAYSTACK_SITECONF = 'tests.testapp.search_sites'
