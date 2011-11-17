from attest import AssertImportHook
from contextlib import contextmanager
from django import get_version
from django.test.simple import DjangoTestSuiteRunner
import warnings


def _fix_for_django():
    version = get_version()
    if version.count('.') >= 2:
        # Turn a.b.c.d.e import a.b
        version = version[:version.index('.', 2)]

    if float(version) <= 1.3:
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

