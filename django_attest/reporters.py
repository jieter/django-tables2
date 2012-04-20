from .environment import testing_environment
from attest import reporters, Tests


def patched(reporter):
    @classmethod
    def test_loader(cls):
        class Loader(object):
            def loadTestsFromNames(self, names, module=None):
                with testing_environment():
                    Tests(names).run(cls)
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
