# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.app.settings'

from attest import Tests
import django_attest
from .columns import columns
from .config import config
from .core import core
from .models import models
from .rows import rows
from .templates import templates
from .utils import utils


loader = django_attest.FancyReporter.test_loader
everything = Tests([columns, config, core, models, rows, templates, utils])


# -----------------------------------------------------------------------------


junit = Tests()

@junit.test
def make_junit_output():
    import xmlrunner
    runner = xmlrunner.XMLTestRunner(output=b'reports')
    runner.run(everything.test_suite())


# -----------------------------------------------------------------------------


pylint = Tests()

@pylint.test
def make_pylint_output():
    from os.path import expanduser
    from pylint.lint import Run
    from pylint.reporters.text import ParseableTextReporter
    if not os.path.exists('reports'):
        os.mkdir('reports')
    with open('reports/pylint.report', 'wb') as handle:
        args = ['django_tables2', 'example', 'tests']
        Run(args, reporter=ParseableTextReporter(output=handle), exit=False)
