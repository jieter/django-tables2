================================================
django-tables2 - An app for creating HTML tables
================================================

.. note::

    Prior to v0.6.0 this package was a fork of miracle2k's and both were known
    as *django-tables*. This caused some problems (e.g. ambiguity and inability
    to put this library on PyPI) so as of v0.6.0 this package is known as
    *django-tables2*.

django-tables2 simplifies the task of turning sets of data into HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
``django.forms`` does for HTML forms. e.g.

.. figure:: http://dl.dropbox.com/u/33499139/django-tables2/example.png
    :align: center
    :alt: An example table rendered using django-tables2


Its features include:

- Any iterable can be a data-source, but special support for Django querysets
  is included.
- The builtin UI does not rely on JavaScript.
- Support for automatic table generation based on a Django model.
- Supports custom column functionality via subclassing.
- Pagination.
- Column based table sorting.
- Template tag to enable trivial rendering to HTML.
- Generic view mixin for use in Django 1.3.

Creating a table is as simple as::

    import django_tables2 as tables

    class SimpleTable(tables.Table):
        class Meta:
            model = Simple

This would then be used in a view::

    def simple_list(request):
        queryset = Simple.objects.all()
        table = SimpleTable(queryset)
        return render_to_response("simple_list.html", {"table": table},
                                  context_instance=RequestContext(request))

And finally in the template::

    {% load django_tables2 %}
    {% render_table table %}


This example shows one of the simplest cases, but django-tables2 can do a lot
more! Check out the `documentation`__ for more details.

.. __: http://django-tables2.readthedocs.org/en/latest/


Building the documentation
==========================

If you want to build the docs from within a virtualenv, and Sphinx is installed
globally, use::

    make html SPHINXBUILD="python $(which sphinx-build)"


Change log
==========

v0.9.2
------

- `SingleTableView` now uses `RequestConfig`. This fixes issues with
  ``order_by_field`, `page_field`, and `per_page_field` not being honored.
- Add `Table.Meta.per_page` and change `Table.paginate` to use it as default.
- Add `title` template filter. It differs from Django's built-in `title` filter
  because it operates on an individual word basis and leaves words containing
  capitals untouched. **Warning**: use `{% load ... from ... %}` to avoid
  inadvertantly replacing Django's builtin `title` template filter.
- `BoundColumn.verbose_name` no longer does `capfirst`, titlising is now the
  responsbility of `Column.header`.
- `BoundColumn.__unicode__` now uses `BoundColumn.header` rather than
  `BoundColumn.verbose_name`.

v0.9.1
------

- Fix version in setup.py (doh)

v0.9.0
------

- Add support for column attributes (see Attrs)
- Add BoundRows.items() to yield (bound_column, cell) pairs
- Tried to make docs more concise. Much stronger promotion of using
  RequestConfig and {% querystring %}

v0.8.4
------

- Removed random 'print' statements.
- Tweaked 'paleblue' theme css to be more flexible
  - removed `whitespace: no-wrap`
  - header background image to support more than 2 rows of text

v0.8.3
------

- Fixed stupid import mistake. Tests didn't pick it up due to them ignoring
  `ImportError`.

v0.8.2
------

- `SingleTableView` now inherits from `ListView` which enables automatic
  `foo_list.html` template name resolution (thanks dramon for reporting)
- `render_table` template tag no suppresses exceptions when `DEBUG=True`

v0.8.1
------

- Fixed bug in render_table when giving it a template (issue #41)

v0.8.0
------

- Added translation support in the default template via `{% trans %}`
- Removed `basic_table.html`, `Table.as_html()` now renders `table.html` but
  will clobber the querystring of the current request. Use the `render_table`
  template tag instead
- `render_table` now supports an optional second argument -- the template to
  use when rendering the table
- `Table` now supports declaring which template to use when rendering to HTML
- Django >=1.3 is now required
- Added support for using django-haystack's `SearchQuerySet` as a data source
- The default template `table.html` now includes block tags to make it easy to
  extend to change small pieces
- Fixed table template parsing problems being hidden due to a subsequent
  exception being raised
- Http404 exceptions are no longer raised during a call to `Table.paginate()`,
  instead it now occurs when `Table.page` is accessed
- Fixed bug where a table couldn't be rendered more than once if it was
  paginated
- Accessing `Table.page` now returns a new page every time, rather than reusing
  a single object

v0.7.8
------

- Tables now support using both ``sequence`` and ``exclude`` (issue #32).
- ``Sequence`` class moved to ``django_tables2/utils.py``.
- Table instances now support modification to the ``exclude`` property.
- Removed ``BoundColumns._spawn_columns``.
- ``Table.data``, ``Table.rows``, and ``Table.columns`` are now attributes
  rather than properties.
