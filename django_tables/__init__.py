# -*- coding: utf8 -*-
# (major, minor, bugfix, "pre-alpha" | "alpha" | "beta" | "final", release | 0)
VERSION = (0, 2, 0, 'alpha', 1)


def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    else:
        if VERSION[3] != 'final':
            version = '%s %s %s' % (version, VERSION[3], VERSION[4])
    return version


# We want to make get_version() available to setup.py even if Django is not
# available or we are not inside a Django project.
try:
    import django
except ImportError:
    import warnings
    warnings.warn('django-tables requires Django, however it is not installed.'
        ' Version information will still be available.')
else:
    try:
        # http://docs.djangoproject.com/en/dev/topics/settings/ says::
        #
        #   If you don't set DJANGO_SETTINGS_MODULE and don't call configure(),
        #   Django will raise an ImportError exception the first time a setting is
        #   accessed.
        #
        from django.conf import settings
        settings.DEBUG  # will raise ImportError if Django isn't configured
    except ImportError:
        # allow get_version() to remain available
        import warnings
        warnings.warn('django-tables requires Django to be configured... but '
            "it isn't! A bunch of stuff won't work :(")

    from tables import *
    from columns import *
