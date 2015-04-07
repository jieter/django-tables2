================================================
django-tables2 - An app for creating HTML tables
================================================

.. image:: https://travis-ci.org/bradleyayers/django-tables2.svg
    :target: https://travis-ci.org/bradleyayers/django-tables2

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

Creating a table is as simple as:

.. code-block:: python

    import django_tables2 as tables

    class SimpleTable(tables.Table):
        class Meta:
            model = Simple

This would then be used in a view:

.. code-block:: python

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


Publishing a release
====================

1. Bump the version in `django-tables2/__init__.py`.
2. Update `README.rst`.
3. Run `python setup.py sdist upload --sign --identity=<your gpg identity>`.

Change log
==========

v0.16.0
-------

- Django 1.8 fixes
- `BoundColumn.verbose_name` now titlises only if no verbose_name was given.
  ``verbose_name`` is used verbatim.
- Add max_length attribute to person CharField
- Add Swedish translation
- Update docs presentation on readthedocs


v0.15.0
-------

- Add UK, Russian, Spanish, Portuguese, and Polish translations
- Add support for computed table ``attrs``.

v0.14.0
-------

- ``querystring`` and ``seturlparam`` template tags now require the request to
  be in the context (backwards incompatible) -- #127
- Add Travis CI support
- Add support for Django 1.5
- Add L10N control for columns #120 (ignored in < Django 1.3)
- Drop Python 2.6.4 support in favour of Python 3.2 support
- Non-queryset data ordering is different between Python 3 and 2. When
  comparing different types, their truth values are now compared before falling
  back to string representations of their type.

v0.13.0
-------

- Add FileColumn.

v0.12.1
-------

- When resolving an accessor, *all* exceptions are smothered into ``None``.

v0.12.0
-------

- Improve performance by removing unnecessary queries
- Simplified pagination:

  - ``Table.page`` is an instance attribute (no longer ``@property``)
  - Exceptions raised by paginators (e.g. ``EmptyPage``) are no longer
    smothered by ``Table.page``
  - Pagination exceptions are raised by ``Table.paginate``
  - ``RequestConfig`` can handles pagination errors silently, can be disabled
    by including ``silent=False`` in the ``paginate`` argument value

- Add ``DateTimeColumn`` and ``DateColumn`` to handle formatting ``datetime``
  and timezones.
- Add ``BooleanColumn`` to handle bool values
- ``render_table`` can now build and render a table for a queryset, rather than
  needing to be passed a table instance
- Table columns created automatically from a model now use specialised columns
- ``Column.render`` is now skipped if the value is considered *empty*, the
  default value is used instead. Empty values are specified via
  ``Column.empty_values``, by default is ``(None, '')`` (backward incompatible)
- Default values can now be specified on table instances or ``Table.Meta``
- Accessor's now honor ``alters_data`` during resolving. Fixes issue that would
  delete all your data when a column had an accessor of ``delete``
- Add ``default`` and ``value`` to context of ``TemplateColumn``
- Add cardinality indication to the pagination area of a table
- ``Attrs`` is deprecated, use ``dict`` instead

v0.11.0
-------

- Add ``URLColumn`` to render URLs in a data source into hyperlinks
- Add ``EmailColumn`` to render email addresses into hyperlinks
- ``TemplateColumn`` can now Django's template loaders to render from a file

v0.10.4
-------

- Fix more bugs on Python 2.6.4, all tests now pass.

v0.10.3
-------

- Fix issues for Python 2.6.4 -- thanks Steve Sapovits & brianmay
- Reduce Django 1.3 dependency to Table.as_html -- thanks brianmay

v0.10.2
-------

- Fix MANIFEST.in to include example templates, thanks TWAC.
- Upgrade django-attest to fix problem with tests on Django 1.3.1

v0.10.1
-------

- Fixed support for Django 1.4's paginator (thanks koledennix)
- Some juggling of internal implementation. `TableData` now supports slicing
  and returns new `TableData` instances. `BoundRows` now takes a single
  argument `data` (a `TableData` instance).
- Add support for `get_pagination` on `SingleTableMixin`.
- `SingleTableMixin` and `SingleTableView` are now importable directly from
  `django_tables2`.

v0.10.0
-------

- Renamed `BoundColumn.order_by` to `order_by_alias` and never returns ``None``
 (**Backwards incompatible**). Templates are affected if they use something
 like:

      {% querystring table.prefixed_order_by_field=column.order_by.opposite|default:column.name %}

  Which should be rewritten as:

      {% querystring table.prefixed_order_by_field=column.order_by_alias.next %}

- Added `next` shortcut to `OrderBy` returned from `BoundColumn.order_by_alias`
- Added `OrderByTuple.get()`
- Deprecated `BoundColumn.sortable`, `Column.sortable`, `Table.sortable`,
  `sortable` CSS class, `BoundColumns.itersortable`, `BoundColumns.sortable`; use `orderable` instead of
  `sortable`.
- Added `BoundColumn.is_ordered`
- Introduced concept of an `order by alias`, see glossary in the docs for details.

v0.9.6
------

- Fix bug that caused an ordered column's th to have no HTML attributes.

v0.9.5
------

- Updated example project to add colspan on footer cell so table border renders
  correctly in Webkit.
- Fix regression that caused 'sortable' class on <th>.
- Table.__init__ no longer *always* calls .order_by() on querysets, fixes #55.
  This does introduce a slight backwards incompatibility. `Table.order_by` now
  has the possibility of returning `None`, previously it would *always* return
  an `OrderByTuple`.
- DeclarativeColumnsMetaclass.__new__ now uses super()
- Testing now requires pylint and Attest >=0.5.3

v0.9.4
------

- Fix regression that caused column verbose_name values that were marked as
  safe to be escaped. Now any verbose_name values that are instances of
  SafeData are used unmodified.

v0.9.3
------

- Fix regression in ``SingleTableMixin``.
- Remove stray `print` statement.

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
