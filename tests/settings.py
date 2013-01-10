from os.path import abspath, dirname, join

ROOT = dirname(abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(ROOT, 'default.sqlite3'),
    },
    'alternate': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(ROOT, 'alternative.sqlite3'),
    }
}

INSTALLED_APPS = [
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'tests.app',
]

SECRET_KEY = 'abcdefghiljklmnopqrstuvwxyz'

ROOT_URLCONF = 'tests.urls'

TEST_RUNNER = 'django_attest.Runner'

TEMPLATE_DIRS = (
    join(ROOT, "templates"),
)

LANGUAGES = (
    ('de', 'German'),
    ('en', 'English'),
)
