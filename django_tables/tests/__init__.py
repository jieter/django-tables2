from attest import Tests
from .core import core
from .templates import templates
from .models import models
#from .memory import memory


tests = Tests([core, templates, models])

def suite():
    return tests.test_suite()

if __name__ == '__main__':
    tests.main()
