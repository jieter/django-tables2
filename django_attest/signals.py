from django.dispatch import Signal

try:
    from django.test.signals import setting_changed
except ImportError:
    # Make our own signal that can be used any library that's interested and
    # wants to work in Django <1.4. Having this allows code to assume
    # `setting_changed` exists, making it simpler.
    setting_changed = Signal(providing_args=["setting", "value"])
