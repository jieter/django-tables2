"""
Allows setting/changing/removing of chosen url query string parameters,
while maintaining any existing others.

Expects the current request to be available in the context as ``request``.

Examples:

    {% set_url_param page=next_page %}
    {% set_url_param page="" %}
    {% set_url_param filter="books" page=1 %}
"""

import urllib
import tokenize
import StringIO
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

class SetUrlParamNode(template.Node):
    def __init__(self, changes):
        self.changes = changes

    def render(self, context):
        request = context.get('request', None)
        if not request: return ""

        # Note that we want params to **not** be a ``QueryDict`` (thus we
        # don't use it's ``copy()`` method), as it would force all values
        # to be unicode, and ``urllib.urlencode`` can't handle that.
        params = dict(request.GET)
        for key, newvalue in self.changes.items():
            newvalue = newvalue.resolve(context)
            if newvalue=='' or newvalue is None: params.pop(key, False)
            else: params[key] = unicode(newvalue)
        # ``urlencode`` chokes on unicode input, so convert everything to
        # utf8. Note that if some query arguments passed to the site have
        # their non-ascii characters screwed up when passed though this,
        # it's most likely not our fault. Django (the ``QueryDict`` class
        # to be exact) uses your projects DEFAULT_CHARSET to decode incoming
        # query strings, whereas your browser might encode the url
        # differently. For example, typing "ä" in my German Firefox's (v2)
        # address bar results in "%E4" being passed to the server (in
        # iso-8859-1), but Django might expect utf-8, where ä would be
        # "%C3%A4"
        def mkstr(s):
            if isinstance(s, list): return map(mkstr, s)
            else: return (isinstance(s, unicode) and [s.encode('utf-8')] or [s])[0]
        params = dict([(mkstr(k), mkstr(v)) for k, v in params.items()])
        # done, return (string is already safe)
        return '?'+urllib.urlencode(params, doseq=True)

def do_seturlparam(parser, token):
    bits = token.contents.split()
    qschanges = {}
    for i in bits[1:]:
        try:
            a, b = i.split('=', 1); a = a.strip(); b = b.strip()
            keys = list(tokenize.generate_tokens(StringIO.StringIO(a).readline))
            if keys[0][0] == tokenize.NAME:
                if b == '""': b = template.Variable('""')  # workaround bug #5270
                else: b = parser.compile_filter(b)
                qschanges[str(a)] = b
            else: raise ValueError
        except ValueError:
            raise template.TemplateSyntaxError, "Argument syntax wrong: should be key=value"
    return SetUrlParamNode(qschanges)

register.tag('set_url_param', do_seturlparam)