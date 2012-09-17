# coding: utf-8
from __future__ import absolute_import, unicode_literals
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

import django_attest
from attest import assert_hook, Tests
from . import contextdecorator, general


loader = django_attest.auto_reporter.test_loader


suite = Tests()
suite.register(contextdecorator.suite)
suite.register(general.suite)


junit = Tests()


@junit.test
def make_junit_output():
    import xmlrunner
    runner = xmlrunner.XMLTestRunner(output=b'reports')
    runner.run(suite.test_suite())
