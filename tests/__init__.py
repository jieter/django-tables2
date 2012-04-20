# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.app.settings'

from attest import assert_hook, Assert, AssertImportHook, COMPILES_AST, Tests
from contextlib import contextmanager
import django
import django_attest
from pkg_resources import parse_version
from tests.app.models import Thing


loader = django_attest.FancyReporter.test_loader
everything = Tests()


@everything.test
def assert_import_hook_enabled_by_default():
    is_buggy_django = parse_version(django.get_version()) < parse_version('1.4')
    if not is_buggy_django and COMPILES_AST:
        assert AssertImportHook.enabled


@everything.test
def test_context_does_transaction_rollback():
    manager = contextmanager(django_attest.TestContext())
    with manager():
        # create a thing, but it should be rolled back when the context exits
        thing = Thing.objects.create(name="foo")

    with Assert.raises(Thing.DoesNotExist):
        Thing.objects.get(pk=thing.pk)


@everything.test
def test_context_supports_fixtures():
    with Assert.raises(Thing.DoesNotExist):
        Thing.objects.get(name="loaded from fixture")

    manager = contextmanager(django_attest.TestContext(fixtures=['tests']))
    with manager():
        Thing.objects.get(name="loaded from fixture")


@everything.test
def template_rendering_tracking_works():
    manager = contextmanager(django_attest.TestContext())
    with manager() as client:
        response = client.get('/')
        assert response.content == "rendered from template.html\n"
        assert [t.name for t in response.templates] == ["template.html"]


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
        args = ['django_attest', 'tests']
        Run(args, reporter=ParseableTextReporter(output=handle), exit=False)
