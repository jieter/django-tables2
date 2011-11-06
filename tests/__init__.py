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
        'haystack',
    ],
    ROOT_URLCONF = 'tests.testapp.urls',
    HAYSTACK_SEARCH_ENGINE = 'simple',
    HAYSTACK_SITECONF = 'tests.testapp.search_sites'
)

from django.test.simple import DjangoTestSuiteRunner
runner = DjangoTestSuiteRunner()
runner.setup_databases()

from .columns import columns
from .config import config
from .core import core
from .models import models
from .rows import rows
from .templates import templates
from .utils import utils

everything = Tests([columns, config, core, models, rows, templates, utils])
