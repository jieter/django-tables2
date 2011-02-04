# -*- coding: utf-8 -*-
__version__ = (0, 2, 0, 'dev')


def get_version():
    version = '%s.%s' % (__version__[0], __version__[1])
    if __version__[2]:
        version = '%s.%s' % (version, __version__[2])
    if __version__[3] != '':
        version = '%s %s' % (version, __version__[3])
    return version

# We want to make get_version() available to setup.py even if Django is not
# available or we are not inside a Django project (so we do distutils stuff).
try:
    # this fails if project settings module isn't configured
    from django.contrib import admin
except ImportError:
    import warnings
    warnings.warn('django-tables requires Django to be configured (settings) '
        'prior to use, however this has not been done. Version information '
        'will still be available.')
else:
    from tables import *
    from columns import *
