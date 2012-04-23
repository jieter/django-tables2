from .environment import testing_environment
from attest import reporters, Tests


def patched(reporter):
    def test_loader(*args, **kwargs):
        class Loader(object):
            def loadTestsFromNames(self, names, module=None):
                with testing_environment():
                    Tests(names).run(reporter)
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
