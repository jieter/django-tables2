from .environment import testing_environment
from attest import reporters, Tests
from django.utils.functional import wraps


def _test_loader_factory(reporter):
    class Loader(object):
        def loadTestsFromNames(self, names, module=None):
            with testing_environment():
                Tests(names).run(reporter)
            raise SystemExit
    return Loader()


class ReporterMixin(object):
    """
    Patch :meth:`test_loader` to perform Django environment configuration.
    """
    @classmethod
    def test_loader(cls):
        return _test_loader_factory(cls)


AbstractReporter = type("AbstractReporter", (ReporterMixin, reporters.AbstractReporter), {})
PlainReporter    = type("PlainReporter",    (ReporterMixin, reporters.PlainReporter), {})
FancyReporter    = type("FancyRepoter",     (ReporterMixin, reporters.FancyReporter), {})
XmlReporter      = type("XmlReporter",      (ReporterMixin, reporters.XmlReporter), {})
QuickFixReporter = type("QuickFixReporter", (ReporterMixin, reporters.QuickFixReporter), {})

@wraps(reporters.auto_reporter)
def auto_reporter(**opts):
    return reporters.auto_reporter(**opts)

auto_reporter.test_loader = lambda: _test_loader_factory(auto_reporter)
