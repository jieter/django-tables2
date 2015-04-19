from contextlib import contextmanager
import lxml.etree
import lxml.html
import warnings


def parse(html):
    return lxml.etree.fromstring(html)


def attrs(xml):
    """
    Helper function that returns a dict of XML attributes, given an element.
    """
    return lxml.html.fromstring(xml).attrib


@contextmanager
def warns(warning_class):
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        yield ws
        assert any((issubclass(w.category, DeprecationWarning) for w in ws))


@contextmanager
def translation(language_code, deactivate=False):
    """
    Port of django.utils.translation.override from Django 1.4

    @param language_code: a language code or ``None``. If ``None``, translation
                          is disabled and raw translation strings are used
    @param    deactivate: If ``True``, when leaving the manager revert to the
                          default behaviour (i.e. ``settings.LANGUAGE_CODE``)
                          rather than the translation that was active prior to
                          entering.
    """
    from django.utils import translation
    original = translation.get_language()
    if language_code is not None:
        translation.activate(language_code)
    else:
        translation.deactivate_all()
    try:
        yield
    finally:
        if deactivate:
            translation.deactivate()
        else:
            translation.activate(original)
