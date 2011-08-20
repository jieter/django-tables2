# -*- coding: utf-8 -*-
from attest import AssertImportHook, Tests

# Django's django.utils.module_loading.module_has_submodule is busted
AssertImportHook.disable()

from django.conf import settings

# It's important to configure prior to importing the tests, as some of them
# import Django's DB stuff.
settings.configure(
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    INSTALLED_APPS = [
        'tests.testapp',
        'django_tables2',
    ],
    ROOT_URLCONF = 'tests.testapp.urls',
)

from django.test.simple import DjangoTestSuiteRunner
runner = DjangoTestSuiteRunner()
runner.setup_databases()

from .core import core
from .templates import templates
from .models import models
from .utils import utils
from .rows import rows
from .columns import columns
from .config import config

everything = Tests([core, templates, models, utils, rows, columns, config])
