from os.path import abspath, dirname, join

ROOT = dirname(abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
    'alternate': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
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

TEMPLATE_DIRS = (
    join(ROOT, "templates"),
)
