# coding: utf-8
__all__ = ()


try:
    # Django 1.2 doesn't have this
    from django.utils import unittest
except ImportError:
    pass
else:
    from attest import capture_output, TestFailure, TestResult, get_reporter_by_name
    from django.test.simple import DjangoTestSuiteRunner


    __all__ += ("Runner", )


    class DummyProgress(object):
        start = update = finish = lambda *a, **k: None


    class TextResult(unittest.TextTestResult):
        def _exc_info_to_string(self, err, test):
            if err[0] is TestFailure:
                # retrieve stdout/stderr
                if self.buffer:
                    stdout = sys.stdout.getvalue().splitlines()
                    stderr = sys.stderr.getvalue().splitlines()
                else:
                    stdout, stderr = [], []

                # pull the test function out of the TestCase.
                test_func = getattr(test, test._testMethodName)
                result = TestResult(test=test_func, exc_info=err, time=0,
                                    error=err[1], stdout=stdout, stderr=stderr)
                reporter = get_reporter_by_name('auto')()
                reporter.begin(())
                reporter.progress = DummyProgress()
                reporter.failure(result)
                with capture_output() as (out, err):
                    try:
                        reporter.finished()
                    except SystemExit:
                        pass
                return '\n'.join(out + err)
            return super(TextResult, self)._exc_info_to_string(err, test)


    class TextRunner(unittest.TextTestRunner):
        resultclass = TextResult


    class Runner(DjangoTestSuiteRunner):
        def run_suite(self, suite, **kwargs):
            runner = TextRunner(verbosity=self.verbosity, failfast=self.failfast)
            return runner.run(suite)
