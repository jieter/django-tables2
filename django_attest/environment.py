from attest import AssertImportHook
from contextlib import contextmanager
import django
from django.test.simple import DjangoTestSuiteRunner
from pkg_resources import parse_version
import warnings


def _fix_for_django():
    if parse_version(django.get_version()) <= parse_version('1.3'):
        warnings.warn("Django <=1.3 has broken import infrastructure, Attest's"
                      " assert hook will be disabled.")
        AssertImportHook.disable()


@contextmanager
def testing_environment():
    """
    Context manager to put Django into a state suitable for testing.
    """
    # patch django bugs
    _fix_for_django()

    # setup test environment
    runner = DjangoTestSuiteRunner()
    runner.setup_test_environment()
    old_config = runner.setup_databases()

    # do stuff
    yield

    # tear down environment
    runner.teardown_databases(old_config)
    runner.teardown_test_environment()

