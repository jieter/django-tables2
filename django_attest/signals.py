# coding: utf-8
from django.core.urlresolvers import clear_url_caches
from django.dispatch import Signal

try:
    from django.test.signals import setting_changed
except ImportError:
    # Make our own signal that can be used any library that's interested and
    # wants to work in Django <1.4. Having this allows code to assume
    # `setting_changed` exists, making it simpler.
    setting_changed = Signal(providing_args=["setting", "value"])


def urlconf_caching(sender, setting, value, **kwargs):
    if setting == "ROOT_URLCONF":
        clear_url_caches()

setting_changed.connect(urlconf_caching)
