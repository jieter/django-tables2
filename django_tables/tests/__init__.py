from attest import Tests
from .core import core
from .templates import templates
#from .memory import memory
#from .models import models

tests = Tests([core, templates])

def suite():
    return tests.test_suite()

if __name__ == '__main__':
    tests.main()
