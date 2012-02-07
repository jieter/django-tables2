# -*- coding: utf-8 -*-
from __future__ import absolute_import
"""
Allows setting/changing/removing of chosen url query string parameters, while
maintaining any existing others.

Expects the current request to be available in the context as ``request``.

Examples:

    {% set_url_param page=next_page %}
    {% set_url_param page="" %}
    {% set_url_param filter="books" page=1 %}

"""
import re
import tokenize
import StringIO
from django.conf import settings
from django import template
from django.template import TemplateSyntaxError, RequestContext, Variable, Node
from django.utils.datastructures import SortedDict
from django.template.loader import get_template, select_template
from django.utils.safestring import mark_safe
from django.utils.http import urlencode
import django_tables2 as tables


register = template.Library()
kwarg_re = re.compile(r"(?:(.+)=)?(.+)")


def token_kwargs(bits, parser):
    """
    Based on Django's ``django.template.defaulttags.token_kwargs``, but with a
    few changes:

    - No legacy mode.
    - Both keys and values are compiled as a filter

    """
    if not bits:
        return {}
    kwargs = SortedDict()
    while bits:
        match = kwarg_re.match(bits[0])
        if not match or not match.group(1):
            return kwargs
        key, value = match.groups()
        del bits[:1]
        kwargs[parser.compile_filter(key)] = parser.compile_filter(value)
    return kwargs


class SetUrlParamNode(Node):
    def __init__(self, changes):
        self.changes = changes

    def render(self, context):
        request = context.get('request', None)
        if not request:
            return ""
        params = dict(request.GET)
        for key, newvalue in self.changes.items():
            newvalue = newvalue.resolve(context)
            if newvalue == '' or newvalue is None:
                params.pop(key, False)
            else:
                params[key] = unicode(newvalue)
        return "?" + urlencode(params, doseq=True)


@register.tag
def set_url_param(parser, token):
    """
    Creates a URL (containing only the querystring [including "?"]) based on
    the current URL, but updated with the provided keyword arguments.

    Example::

        {% set_url_param name="help" age=20 %}
        ?name=help&age=20

    **Deprecated** as of 0.7.0, use ``updateqs``.
    """
    bits = token.contents.split()
    qschanges = {}
    for i in bits[1:]:
        try:
            a, b = i.split('=', 1)
            a = a.strip()
            b = b.strip()
            a_line_iter = StringIO.StringIO(a).readline
            keys = list(tokenize.generate_tokens(a_line_iter))
            if keys[0][0] == tokenize.NAME:
                # workaround bug #5270
                b = Variable(b) if b == '""' else parser.compile_filter(b)
                qschanges[str(a)] = b
            else:
                raise ValueError
        except ValueError:
            raise TemplateSyntaxError("Argument syntax wrong: should be"
                                      "key=value")
    return SetUrlParamNode(qschanges)


class QuerystringNode(Node):
    def __init__(self, params):
        self.params = params

    def render(self, context):
        request = context.get('request', None)
        if not request:
            return ""
        params = dict(request.GET)
        for key, value in self.params.iteritems():
            key = key.resolve(context)
            value = value.resolve(context)
            if key not in ("", None):
                params[key] = value
        return "?" + urlencode(params, doseq=True)


# {% querystring "name"="abc" "age"=15 %}
@register.tag
def querystring(parser, token):
    """
    Creates a URL (containing only the querystring [including "?"]) derived
    from the current URL's querystring, by updating it with the provided
    keyword arguments.

    Example (imagine URL is ``/abc/?gender=male&name=Brad``)::

        {% querystring "name"="Ayers" "age"=20 %}
        ?name=Ayers&gender=male&age=20

    """
    bits = token.split_contents()
    tag = bits.pop(0)
    try:
        return QuerystringNode(token_kwargs(bits, parser))
    finally:
        # ``bits`` should now be empty, if this is not the case, it means there
        # was some junk arguments that token_kwargs couldn't handle.
        if bits:
            raise TemplateSyntaxError("Malformed arguments to '%s'" % tag)


class RenderTableNode(Node):
    """
    :param    table: the table to render
    :type     table: Table object
    :param template: Name[s] of template to render
    :type  template: unicode or list
    """
    def __init__(self, table, template=None):
        self.table = table
        self.template = template

    def render(self, context):
        table = self.table.resolve(context)
        if not isinstance(table, tables.Table):
            raise ValueError("Expected Table object, but didn't find one.")
        if "request" not in context:
            raise AssertionError(
                    "{% render_table %} requires that the template context"
                    " contains the HttpRequest in a 'request' variable,"
                    " check your TEMPLATE_CONTEXT_PROCESSORS setting.")
        request = context['request']
        context = RequestContext(request, {"table": table})
        if self.template:
            template = self.template.resolve(context)
        else:
            template = table.template
        if isinstance(template, basestring):
            template = get_template(template)
        else:
            # assume some iterable was given
            template = select_template(template)
        try:
            table.request = request  # HACK! :(
            return template.render(context)
        finally:
            del table.request

@register.tag
def render_table(parser, token):
    bits = token.split_contents()
    try:
        tag, table = bits.pop(0), parser.compile_filter(bits.pop(0))
    except ValueError:
        raise TemplateSyntaxError("'%s' must be given a table." % bits[0])
    template = parser.compile_filter(bits.pop(0)) if bits else None
    return RenderTableNode(table, template)
