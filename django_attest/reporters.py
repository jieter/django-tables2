from attest import reporters, Tests
from django.test.simple import DjangoTestSuiteRunner
from .patches import apply_django_fixes


def patched(reporter):
    @classmethod
    def test_loader(cls):
        class Loader(object):
            def loadTestsFromNames(self, names, module=None):
                # patch django bugs
                apply_django_fixes()
                # setup test environment
                runner = DjangoTestSuiteRunner()
                runner.setup_test_environment()
                old_config = runner.setup_databases()
                # run tests
                Tests(names).run(cls)
                # tear down environment
                runner.teardown_databases(old_config)
                runner.teardown_test_environment()
                raise SystemExit
        return Loader()
    reporter.test_loader = test_loader
    return reporter


AbstractReporter = patched(reporters.AbstractReporter)
PlainReporter    = patched(reporters.PlainReporter)
FancyReporter    = patched(reporters.FancyReporter)
auto_reporter    = patched(reporters.auto_reporter)
XmlReporter      = patched(reporters.XmlReporter)
QuickFixReporter = patched(reporters.QuickFixReporter)
