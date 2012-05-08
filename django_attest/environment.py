from attest import AssertImportHook, COMPILES_AST
from contextlib import contextmanager
import django
from django.test.simple import DjangoTestSuiteRunner
import logging
from pkg_resources import parse_version


logger = logging.getLogger("django_attest")


if parse_version(django.get_version()) < parse_version('1.4'):
    logger.info("Django <1.4 has broken import infrastructure, Attest's"
                " assert hook will be disabled.")
    AssertImportHook.disable()
elif COMPILES_AST:
    AssertImportHook.enable()


@contextmanager
def testing_environment():
    """
    Context manager to put Django into a state suitable for testing.
    """
    # setup test environment
    runner = DjangoTestSuiteRunner()
    runner.setup_test_environment()
    old_config = runner.setup_databases()

    # do stuff
    yield

    # tear down environment
    runner.teardown_databases(old_config)
    runner.teardown_test_environment()

