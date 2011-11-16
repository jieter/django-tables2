from django import get_version
import warnings


def apply_django_fixes():
    version = get_version()
    if version.count('.') >= 2:
        # Turn a.b.c.d.e import a.b
        version = version[:version.index('.', 2)]

    if float(version) <= 1.3:
        warnings.warn("Django <=1.3 has broken import infrastructure, Attest's"
                      " assert hook will be disabled.")
        from attest import AssertImportHook
        AssertImportHook.disable()
