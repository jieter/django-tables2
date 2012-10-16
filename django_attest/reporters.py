# coding: utf-8
from .environment import setup
from attest import reporters
import sys


__all__ = ("auto_reporter", "AbstractReporter", "FancyReporter",
           "PlainReporter", "QuickFixReporter", "XmlReporter")


class ReporterMixin(object):
    """
    A mixin for reporters that handles setting up a Django environment.
    """
    def begin(self, tests):
        self.teardown = setup()
        return super(ReporterMixin, self).begin(tests)

    def finished(self):
        self.teardown()
        return super(ReporterMixin, self).finished()


def patched(reporter):
    return type(reporter.__name__,
                (ReporterMixin, reporter),
                {})


AbstractReporter = patched(reporters.AbstractReporter)
PlainReporter    = patched(reporters.PlainReporter)
FancyReporter    = patched(reporters.FancyReporter)
XmlReporter      = patched(reporters.XmlReporter)
QuickFixReporter = patched(reporters.QuickFixReporter)


def auto_reporter(**opts):
    # Let Attest make the decision, then return our own version. This only
    # works because we name our reporters the same as Attest
    suggested = reporters.auto_reporter(**opts)
    return getattr(sys.modules[__name__], type(suggested).__name__)
