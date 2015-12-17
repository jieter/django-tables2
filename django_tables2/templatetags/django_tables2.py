# coding: utf-8
from __future__ import absolute_import, unicode_literals

import re
import tokenize
from collections import OrderedDict

import six
from django import template
from django.core.exceptions import ImproperlyConfigured
from django.template import Node, TemplateSyntaxError, Variable
from django.template.defaultfilters import title as old_title
from django.template.defaultfilters import stringfilter
from django.template.loader import get_template, select_template
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

import django_tables2 as tables
from django_tables2.config import RequestConfig

register = template.Library()
kwarg_re = re.compile(r"(?:(.+)=)?(.+)")
context_processor_error_msg = (
    "{%% %s %%} requires django.core.context_processors.request "
    "to be in your settings.TEMPLATE_CONTEXT_PROCESSORS in order for "
    "the included template tags to function correctly."
)


def token_kwargs(bits, parser):
    """
    Based on Django's `~django.template.defaulttags.token_kwargs`, but with a
    few changes:

    - No legacy mode.
    - Both keys and values are compiled as a filter
    """
    if not bits:
        return {}
    kwargs = OrderedDict()
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
        super(SetUrlParamNode, self).__init__()
        self.changes = changes

    def render(self, context):
        if not 'request' in context:
            raise ImproperlyConfigured(context_processor_error_msg
                                       % 'set_url_param')
        params = dict(context['request'].GET)
        for key, newvalue in self.changes.items():
            newvalue = newvalue.resolve(context)
            if newvalue == '' or newvalue is None:
                params.pop(key, False)
            else:
                params[key] = six.text_type(newvalue)
        return "?" + urlencode(params, doseq=True)


@register.tag
def set_url_param(parser, token):
    """
    Creates a URL (containing only the querystring [including "?"]) based on
    the current URL, but updated with the provided keyword arguments.

    Example::

        {% set_url_param name="help" age=20 %}
        ?name=help&age=20

    **Deprecated** as of 0.7.0, use `querystring`.
    """
    bits = token.contents.split()
    qschanges = {}
    for i in bits[1:]:
        try:
            key, value = i.split('=', 1)
            key = key.strip()
            value = value.strip()
            key_line_iter = six.StringIO(key).readline
            keys = list(tokenize.generate_tokens(key_line_iter))
            if keys[0][0] == tokenize.NAME:
                # workaround bug #5270
                value = Variable(value) if value == '""' else parser.compile_filter(value)
                qschanges[str(key)] = value
            else:
                raise ValueError
        except ValueError:
            raise TemplateSyntaxError("Argument syntax wrong: should be"
                                      "key=value")
    return SetUrlParamNode(qschanges)


class QuerystringNode(Node):
    def __init__(self, updates, removals):
        super(QuerystringNode, self).__init__()
        self.updates = updates
        self.removals = removals

    def render(self, context):
        if not 'request' in context:
            raise ImproperlyConfigured(context_processor_error_msg
                                       % 'querystring')
        params = dict(context['request'].GET)
        for key, value in self.updates.items():
            key = key.resolve(context)
            value = value.resolve(context)
            if key not in ("", None):
                params[key] = value
        for removal in self.removals:
            params.pop(removal.resolve(context), None)
        return escape("?" + urlencode(params, doseq=True))


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
        {% querystring "name"="Ayers" without "gender" %}
        ?name=Ayers

    """
    bits = token.split_contents()
    tag = bits.pop(0)
    updates = token_kwargs(bits, parser)
    # ``bits`` should now be empty of a=b pairs, it should either be empty, or
    # have ``without`` arguments.
    if bits and bits.pop(0) != "without":
        raise TemplateSyntaxError("Malformed arguments to '%s'" % tag)
    removals = [parser.compile_filter(bit) for bit in bits]
    return QuerystringNode(updates, removals)


class RenderTableNode(Node):
    """
    :param    table: the table to render
    :type     table: Table object
    :param template: Name[s] of template to render
    :type  template: unicode or list
    """
    def __init__(self, table, template=None):
        super(RenderTableNode, self).__init__()
        self.table = table
        self.template = template

    def render(self, context):
        table = self.table.resolve(context)

        if isinstance(table, tables.Table):
            pass
        elif hasattr(table, "model"):
            queryset = table

            # We've been given a queryset, create a table using its model and
            # render that.
            class OnTheFlyTable(tables.Table):
                class Meta:
                    model = queryset.model
                    attrs = {"class": "paleblue"}
            table = OnTheFlyTable(queryset)
            request = context.get('request')
            if request:
                RequestConfig(request).configure(table)
        else:
            raise ValueError("Expected table or queryset, not '%s'." %
                             type(table).__name__)

        if self.template:
            template = self.template.resolve(context)
        else:
            template = table.template

        if isinstance(template, six.string_types):
            template = get_template(template)
        else:
            # assume some iterable was given
            template = select_template(template)

        # Contexts are basically a `MergeDict`, when you `update()`, it
        # internally just adds a dict to the list to attempt lookups from. This
        # is why we're able to `pop()` later.
        context.update({"table": table})
        try:
            # HACK:
            # TemplateColumn benefits from being able to use the context
            # that the table is rendered in. The current way this is
            # achieved is to temporarily attach the context to the table,
            # which TemplateColumn then looks for and uses.
            table.context = context
            return template.render(context.flatten())
        finally:
            del table.context
            context.pop()

@register.tag
def render_table(parser, token):
    """
    Render a HTML table.

    The tag can be given either a `.Table` object, or a queryset. An optional
    second argument can specify the template to use.

    Example::

        {% render_table table %}
        {% render_table table "custom.html" %}
        {% render_table user_queryset %}

    When given a queryset, a `.Table` class is generated dynamically as
    follows::

        class OnTheFlyTable(tables.Table):
            class Meta:
                model = queryset.model
                attrs = {"class": "paleblue"}

    For configuration beyond this, a `.Table` class must be manually defined,
    instantiated, and passed to this tag.

    The context should include a *request* variable containing the current
    request. This allows pagination URLs to be created without clobbering the
    existing querystring.
    """
    bits = token.split_contents()
    try:
        tag, table = bits.pop(0), parser.compile_filter(bits.pop(0))
    except ValueError:
        raise TemplateSyntaxError("'%s' must be given a table or queryset."
                                  % bits[0])
    template = parser.compile_filter(bits.pop(0)) if bits else None
    return RenderTableNode(table, template)


class NoSpacelessNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
        super(NoSpacelessNode, self).__init__()

    def render(self, context):
        return mark_safe(re.sub(r'>\s+<', '>&#32;<',
                                self.nodelist.render(context)))

@register.tag
def nospaceless(parser, token):
    nodelist = parser.parse(('endnospaceless',))
    parser.delete_first_token()
    return NoSpacelessNode(nodelist)


RE_UPPERCASE = re.compile('[A-Z]')


@register.filter
@stringfilter
def title(value):
    """
    A slightly better title template filter.

    Same as Django's builtin `~django.template.defaultfilters.title` filter,
    but operates on individual words and leaves words unchanged if they already
    have a capital letter.
    """
    title_word = lambda w: w if RE_UPPERCASE.search(w) else old_title(w)
    return re.sub('(\S+)', lambda m: title_word(m.group(0)), value)
title.is_safe = True


# Django 1.2 doesn't include the l10n template tag library (and it's non-
# trivial to implement) so for Django 1.2 the localize functionality is
# disabled.
try:
    from django.templatetags.l10n import register as l10n_register
except ImportError:
    localize = unlocalize = lambda x: x  # no-op
else:
    localize = l10n_register.filters['localize']
    unlocalize = l10n_register.filters['unlocalize']

register.filter('localize', localize)
register.filter('unlocalize', unlocalize)
