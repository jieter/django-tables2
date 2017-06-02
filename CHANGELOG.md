# Change log

## master (unreleased)


## 1.7.1 (2017-06-02)
- Call before_render when rendering with the render_table template tag (fixes [#447](https://github.com/bradleyayers/django-tables2/issues/447))

## 1.7.0 (2017-06-01)
 - Make `title()` lazy ([#443](https://github.com/bradleyayers/django-tables2/pull/443) by [@ygwain](https://github.com/ygwain), fixes [#438](https://github.com/bradleyayers/django-tables2/issues/438))
 - Fix `__all__` by populating them with the names of the items to export instead of the items themself.
 - Allow adding extra columns to an instance using the `extra_columns` argument. Fixes [#403](https://github.com/bradleyayers/django-tables2/issues/403), [#70](https://github.com/bradleyayers/django-tables2/issues/70)
 - Added a hook `before_render` to allow last-minute changes to the table before rendering.
 - Added `BoundColumns.show()` and `BoundColumns.hide()` to show/hide columns on an instance of a `Table`.
 - Use `<listlike>.verbose_name`/`.verbose_name_plural` if it exists to name the items in the list. (fixes [#166](https://github.com/bradleyayers/django-tables2/issues/166))

## 1.6.1 (2017-05-08)
 - Add missing pagination to the responsive bootstrap template ([#440](https://github.com/bradleyayers/django-tables2/pull/440) by [@tobiasmcnulty](https://github.com/tobiasmcnulty))

## 1.6.0 (2017-05-01)
 - Add new template `bootstrap-responsive.html` to generate a responsive bootstrap table. (Fixes [#436](https://github.com/bradleyayers/django-tables2/issues/436))

## 1.5.0 (2017-04-18)
_Full disclosure: as of april 1st, 2017, I am an employee of [Zostera](http://zostera.nl/), as such I will continue to maintain and improve django-tables2._
 - Made `TableBase.as_values()` an interator ([#432](https://github.com/bradleyayers/django-tables2/pull/432) by [@pziarsolo](https://github.com/pziarsolo))
 - Added `JSONField` for data in JSON format.
 - Added `__all__` in `django_tables2/__init__.py` and `django_tables2/columns/__init__.py`
 - Added a setting `DJANGO_TABLES2_TEMPLATE` to allow project-wide overriding of the template used to render tables (fixes [#434](https://github.com/bradleyayers/django-tables2/issues/434)).

## 1.4.2 (2017-03-06)
 - Feature: Pinned rows ([#411](https://github.com/bradleyayers/django-tables2/pull/411) by [@djk2](https://github.com/djk2), fixes [#406](https://github.com/bradleyayers/django-tables2/issues/406))
 - Fix an issue where `ValueError` was raised while using a view with a `get_queryset()` method defined. (fix with [#423](https://github.com/bradleyayers/django-tables2/pull/423) by [@desecho](https://github.com/desecho))

## 1.4.1 (2017-02-27)
 - Fix urls to screenshots in on pypi description (fixes [ #398](https://github.com/bradleyayers/django-tables2/issues/398))
 - Prevent superfluous spaces when a callable `row_attrs['class']` returns an empty string ([#417](https://github.com/bradleyayers/django-tables2/pull/417 by [@Superman8218](https://github.com/Superman8218)), fixes [#416](https://github.com/bradleyayers/django-tables2/issues/416))


## 1.4.0 (2017-02-27)
 - Return `None` from `Table.as_values()` for missing values. [#419](https://github.com/bradleyayers/django-tables2/pull/419)
 - Fix ordering by custom fields, and refactor `TableData` [#424](https://github.com/bradleyayers/django-tables2/pull/424), fixes [#413](https://github.com/bradleyayers/django-tables2/issues/413)
 - Revert removing `TableData.__iter__()` (removed in [this commit](https://github.com/bradleyayers/django-tables2/commit/8fe9826429e6945a9258bc181fcbd711b282dba9)), fixes [#427](https://github.com/bradleyayers/django-tables2/issues/427), [#361](https://github.com/bradleyayers/django-tables2/issues/361) and [#421](https://github.com/bradleyayers/django-tables2/issues/421).

## 1.3.0 (2017-01-20)
 - Implement method `Table.as_values()` to get it's raw values. [#394](https://github.com/bradleyayers/django-tables2/pull/394) by [@intiocean](https://github.com/intiocean)
 - Fix some compatibility issues with django 2.0 [#408](https://github.com/bradleyayers/django-tables2/pull/409) by [djk2](https://github.com/djk2)

## 1.2.9 (2016-12-21)
 - Documentation for `None`-column attributes [#401](https://github.com/bradleyayers/django-tables2/pull/401) by [@dyve](https://github.com/dyve)

## 1.2.8 (2016-12-21)
 - `None`-column attributes on child class overwrite column attributes of parent class
 [#400](https://github.com/bradleyayers/django-tables2/pull/400) by [@dyve](https://github.com/dyve)

## 1.2.7 (2016-12-12)
- Apply `title` to a column's `verbose_name` when it is derived from a model, fixes [#249](https://github.com/bradleyayers/django-tables2/issues/249). ([#382](https://github.com/bradleyayers/django-tables2/pull/382) by [@shawnnapora](https://github.com/shawnnapora))
- Update documentation after deprecation of `STATIC_URL` in django ([#384](https://github.com/bradleyayers/django-tables2/pull/384), by [@velaia](https://github.com/velaia))
- Cleanup of the templates, making the output more equal ([#381](https://github.com/bradleyayers/django-tables2/pull/381) by [@ralgozino](https://github.com/ralgozino))
- Use new location for `urlresolvers` in Django and add backwards compatible import ([#388](https://github.com/bradleyayers/django-tables2/pull/388) by [@felixxm](https://github.com/felixxm))
- Fix a bug where using `sequence` and then `exclude` in a child table would result in a `KeyError`
- Some documentation fixes and cleanups.

## 1.2.6 (2016-09-06)
- Added `get_table_kwargs()` method to `SingleTableMixin` to allow passing custom keyword arguments to the `Table` constructor. ([#366](https://github.com/bradleyayers/django-tables2/pull/366) by [@fritz-k](https://github.com/fritz-k))
- Allow the children of `TableBase` render in the `{% render_table %}` template tag. ([#377](https://github.com/bradleyayers/django-tables2/pull/377) by [@shawnnapora](https://github.com/shawnnapora))
- Refactor `BoundColumn` attributes to allow override of CSS class names, fixes [#349](https://github.com/bradleyayers/django-tables2/issues/349) ([#370](https://github.com/bradleyayers/django-tables2/pull/370) by [@graup](https://github.com/graup)). Current behaviour should be intact, we will change the default in the future so it will **not** add the column name to the list of CSS classes.

## 1.2.5 (2016-07-30)
- Fixed an issue preventing the rest of the row being rendered if a `BooleanColumn` was in the table for a model without custom choices defined on the model field. ([#360](https://github.com/bradleyayers/django-tables2/issues/360))

## 1.2.4 (2016-07-28)
- Added Norwegian Locale ([#356](https://github.com/bradleyayers/django-tables2/issues/356) by [@fanzypantz](https://github.com/fanzypantz))
- Restore default pagination for `SingleTableMixin`, fixes [#354](https://github.com/bradleyayers/django-tables2/issues/354) ([#395](https://github.com/bradleyayers/django-tables2/pull/359) by [@graup](https://github.com/graup))

## 1.2.3 (2016-07-05)
 - Accept `text` parameter in `FileColumn`, analogous to `LinkColumn` ([#343](https://github.com/bradleyayers/django-tables2/pull/343) by [@graup](https://github.com/graup))
 - Fix TemplateColumn RemovedInDjango110Warning fixes [#346](https://github.com/bradleyayers/django-tables2/issues/346).
 - Use field name in RelatedColumnLink ([#350](https://github.com/bradleyayers/django-tables2/pull/350), fixes [#347](https://github.com/bradleyayers/django-tables2/issues/347))

## v1.2.2 (2016-06-04)
- Allow use of custom class names for ordered columns through `attrs`. (
[#329](https://github.com/bradleyayers/django-tables2/pull/329) by [@theTarkus](https://github.com/theTarkus))
- Column ordering queryset passthrough ([#330](https://github.com/bradleyayers/django-tables2/pull/330) by [@theTarkus](https://github.com/theTarkus))
- Cleanup/restructuring of [documentation](http://django-tables2.readthedocs.io/), ([#325](https://github.com/bradleyayers/django-tables2/pull/325))
- Fixed an issue where explicitly defined column options where not preserved over inheritance ([#339](https://github.com/bradleyayers/django-tables2/pull/339), [issue #337](https://github.com/bradleyayers/django-tables2/issues/337))
- Fixed an issue where `exclude` in combination with `sequence` raised a KeyError ([#341](https://github.com/bradleyayers/django-tables2/pull/341), [issue #205](https://github.com/bradleyayers/django-tables2/issues/205))

## v1.2.1 (2016-05-09)
- table footers (#323)
- Non-field based `LinkColumn` only renders default value if lookup fails. (#322)
- Accept `text` parameter in `BaseLinkColumn`-based columns. (#322)
- Pass the table instance into SingleTableMixin's get_table_pagination (#320 by [@georgema1982](https://github.com/georgema1982), fixes #319)
- Check if the view has `paginate_by` before before trying to access it. (fixes #326)

## v1.2.0 (2016-05-02)
- Allow custom attributes for rows (fixes #47)

## v1.1.8 (2016-05-02)
- Pass the table instance into `SingleTableMixin.get_table_pagination()` (#320 by
(@georgema1982)[https://github.com/georgema1982])
- Ability to change the body of the `<a>`-tag, by passing `text` kwarg to the columns inheriting from BaseLinkColumn (#318 by [@desecho](https://github.com/desecho), #322)
- Non-field based LinkColumn only renders default value if lookup fails and text is not set. (#322, fixes #257)

## v1.1.7 (2016-04-26)
- Added Italian translation (#315 by [@paolodina](https://github.com/paolodina)
- Added Dutch translation.
- Fixed {% blocktrans %} template whitespace issues
- Fixed errors when using a column named `items` (#316)
- Obey `paginate_by` (from `MultipleObjectMixin`) if no later pagination is defined (#242)

## v1.1.6 (2016-04-02)
- Correct error message about request context processors for current Django (#314)
- Skipped 1.1.5 due to an error while creating the tag.

## v1.1.4 (2016-03-22)
- Fix broken `setup.py` if Django is not installed before django-tables2 (fixes #312)

## v1.1.3 (2016-03-21)
- Drop support for Django 1.7
- Add argument to CheckBoxColumn to render it as checked (original PR: #208)

## v1.1.2 (2016-02-16)
- Fix `BooleanColumn` with choices set will always render as if `True` (#301)
- Fix a bug with `TemplateColumn` while using cached template loader (#75)

## v1.1.1 (2016-01-26)
- Allow Meta.fields to be a list as well as a tuple (#250)
- Call template.render with a dict in Django >= 1.8. (#298)
- Added `RelatedLinkColumn()` to render links to related objects (#297)
- Remove default value from request param to table.as_html()

## v1.1.0 (2016-01-19)
- Add tests for `TimeColumn`
- Remove `sortable` argument for `Table` and Column constructors and its associated methods. Deprecated since 2012.
- Remove deprecated aliases for `attrs` in `CheckboxColumn`.
- Remove deprecated `OrderByTuple` `cmp` method (deprecated since 2013).
- Add bootstrap template and (#293, fixes #141, #285)
- Fix different html for tables with and without pagination (#293, fixes #149, #285)
- Remove `{% nospaceless %}` template tag and remove wrapping template in `{% spaceless %}` **Possible breaking change**, if you use custom templates.

## v1.0.7 (2016-01-03)
- Explicitly check if `column.verbose_name` is not None to support empty column headers (fixes #280)
- Cleanup the example project to make it work with modern Django versions.
- Do not sort queryset when orderable=False (#204 by [@bmihelac](https://github.com/bmihelac))
- `show_header` attribute on `Table` allows disabling the header (#175 by [@kviktor](https://github.com/kviktor))
- `LinkColumn` now tries to call `get_absolute_url` on a record if no `viewname` is provided (#283, fixes #231).
- Add `request` argument to `Table.as_html()` to allow passing correct request objects instead of poorly generated ones #282
- Add coverage reporting to build #282
- Drop support for python 3.2 (because of coverage), support ends feb 2016 #282
- move `build_request` from `django_table2.utils` to `tests.utils` and amend tests #282

## v1.0.6 (2015-12-29)
- Support for custom text value in LinkColumn (#277 by [@toudi](https://github.com/toudi))
- Refactor LinkColumn.render_link() to not escape twice #279
- Removed `Attrs` (wrapper for dict), deprecated on 2012-09-18
- Convert README.md to rst in setup.py to make PyPI look nice (fixes #97)

## v1.0.5 (2015-12-17)
- First version released by new maintainer [@jieter](https://github.com/jieter)
- Dropped support for django 1.5 and 1.6, add python 3.5 with django 1.8 and 1.9 to the build matrix (#273)
- Prevent `SingleTableView` from calling `get_queryset` twice. (fixes #155)
- Don't call managers when resolving accessors. (#214 by [@mbertheau](https://github.com/mbertheau), fixes #211)

## v1.0.4 (2015-05-09)
- Fix bug in retrieving `field.verbose_name` under Django 1.8.

## v1.0.3
- Remove setup.cfg as PyPI doesn't actually support it, instead it's a distutils2 thing that's been discontinued.

## v1.0.2
- Add setup.cfg to declare README.md for PyPI.

## v1.0.1
- Convert README to markdown so it's formatted nicely on PyPI.

## v1.0.0
- Travis CI builds pass.
- Added Python 3.4 support.
- Added Django 1.7 and Django 1.8 support.
- Convert tests to using py.test.

## v0.16.0
- Django 1.8 fixes
- `BoundColumn.verbose_name` now titlises only if no verbose_name was given. `verbose_name` is used verbatim.
- Add max_length attribute to person CharField
- Add Swedish translation
- Update docs presentation on readthedocs


## v0.15.0
- Add UK, Russian, Spanish, Portuguese, and Polish translations
- Add support for computed table `attrs`.

## v0.14.0
- `querystring` and `seturlparam` template tags now require the request to be in the context (backwards incompatible) -- #127
- Add Travis CI support
- Add support for Django 1.5
- Add L10N control for columns #120 (ignored in < Django 1.3)
- Drop Python 2.6.4 support in favour of Python 3.2 support
- Non-queryset data ordering is different between Python 3 and 2. When comparing different types, their truth values are now compared before falling back to string representations of their type.

## v0.13.0
- Add FileColumn.

## v0.12.1
- When resolving an accessor, *all* exceptions are smothered into `None`.

## v0.12.0
 - Improve performance by removing unnecessary queries
 - Simplified pagination:
    - `Table.page` is an instance attribute (no longer `@property`)
    - Exceptions raised by paginators (e.g. `EmptyPage`) are no longer
      smothered by `Table.page`
    - Pagination exceptions are raised by `Table.paginate`
    - `RequestConfig` can handles pagination errors silently, can be disabled
      by including `silent=False` in the `paginate` argument value
 - Add `DateTimeColumn` and `DateColumn` to handle formatting `datetime`
   and timezones.
 - Add `BooleanColumn` to handle bool values
 - `render_table` can now build and render a table for a queryset, rather than
   needing to be passed a table instance
 - Table columns created automatically from a model now use specialised columns
 - `Column.render` is now skipped if the value is considered *empty*, the
   default value is used instead. Empty values are specified via
   `Column.empty_values`, by default is `(None, '')` (backward incompatible)
 - Default values can now be specified on table instances or `Table.Meta`
 - Accessor's now honor `alters_data` during resolving. Fixes issue that would
   delete all your data when a column had an accessor of `delete`
 - Add `default` and `value` to context of `TemplateColumn`
 - Add cardinality indication to the pagination area of a table
 - `Attrs` is deprecated, use `dict` instead

## v0.11.0
 - Add `URLColumn` to render URLs in a data source into hyperlinks
 - Add `EmailColumn` to render email addresses into hyperlinks
 - `TemplateColumn` can now Django's template loaders to render from a file

## v0.10.4
 - Fix more bugs on Python 2.6.4, all tests now pass.

## v0.10.3
 - Fix issues for Python 2.6.4 -- thanks Steve Sapovits & brianmay
 - Reduce Django 1.3 dependency to Table.as_html -- thanks brianmay

## v0.10.2
 - Fix MANIFEST.in to include example templates, thanks TWAC.
 - Upgrade django-attest to fix problem with tests on Django 1.3.1

## v0.10.1
 - Fixed support for Django 1.4's paginator (thanks koledennix)
 - Some juggling of internal implementation.
   `TableData` now supports slicing and returns new `TableData` instances.
   `BoundRows` now takes a single argument `data` (a `TableData` instance).
 - Add support for `get_pagination` on `SingleTableMixin`.
 - `SingleTableMixin` and `SingleTableView` are now importable directly from `django_tables2`.

## v0.10.0
 - Renamed `BoundColumn.order_by` to `order_by_alias` and never returns `None`
   (**Backwards incompatible**). Templates are affected if they use something like:

       {% querystring table.prefixed_order_by_field=column.order_by.opposite|default:column.name %}

   Which should be rewritten as:

       {% querystring table.prefixed_order_by_field=column.order_by_alias.next %}

 - Added `next` shortcut to `OrderBy` returned from `BoundColumn.order_by_alias`
 - Added `OrderByTuple.get()`
 - Deprecated `BoundColumn.sortable`, `Column.sortable`, `Table.sortable`,
   `sortable` CSS class, `BoundColumns.itersortable`, `BoundColumns.sortable`; use `orderable` instead of `sortable`.
 - Added `BoundColumn.is_ordered`
 - Introduced concept of an `order by alias`, see glossary in the docs for details.

## v0.9.6
 - Fix bug that caused an ordered column's th to have no HTML attributes.

## v0.9.5
 - Updated example project to add colspan on footer cell so table border renders correctly in Webkit.
 - Fix regression that caused 'sortable' class on <th>.
 - Table.__init__ no longer *always* calls .order_by() on querysets, fixes #55.
   This does introduce a slight backwards incompatibility. `Table.order_by` now has the possibility of returning `None`, previously it would *always* return an `OrderByTuple`.
 - DeclarativeColumnsMetaclass.__new__ now uses super()
 - Testing now requires pylint and Attest >=0.5.3

## v0.9.4
 - Fix regression that caused column verbose_name values that were marked as
   safe to be escaped. Now any verbose_name values that are instances of
   SafeData are used unmodified.

## v0.9.3
 - Fix regression in `SingleTableMixin`.
 - Remove stray `print` statement.

## v0.9.2
 - `SingleTableView` now uses `RequestConfig`. This fixes issues with
   `order_by_field`, `page_field`, and `per_page_field` not being honored.
 - Add `Table.Meta.per_page` and change `Table.paginate` to use it as default.
 - Add `title` template filter. It differs from Django's built-in `title` filter
   because it operates on an individual word basis and leaves words containing
   capitals untouched. **Warning**: use `{% load ... from ... %}` to avoid
   inadvertantly replacing Django's builtin `title` template filter.
 - `BoundColumn.verbose_name` no longer does `capfirst`, titlising is now the
   responsbility of `Column.header`.
 - `BoundColumn.__unicode__` now uses `BoundColumn.header` rather than
   `BoundColumn.verbose_name`.

## v0.9.1
 - Fix version in setup.py (doh)

## v0.9.0
 - Add support for column attributes (see Attrs)
 - Add BoundRows.items() to yield (bound_column, cell) pairs
 - Tried to make docs more concise. Much stronger promotion of using
   RequestConfig and {% querystring %}

## v0.8.4
 - Removed random 'print' statements.
 - Tweaked 'paleblue' theme css to be more flexible:
   - removed `whitespace: no-wrap`
   - header background image to support more than 2 rows of text

## v0.8.3
 - Fixed stupid import mistake. Tests didn't pick it up due to them ignoring `ImportError`.

## v0.8.2
 - `SingleTableView` now inherits from `ListView` which enables automatic
   `foo_list.html` template name resolution (thanks dramon for reporting)
 - `render_table` template tag no suppresses exceptions when `DEBUG=True`

## v0.8.1
 - Fixed bug in render_table when giving it a template (issue #41)

## v0.8.0
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

## v0.7.8
 - Tables now support using both `sequence` and `exclude` (issue #32).
 - `Sequence` class moved to `django_tables2/utils.py`.
 - Table instances now support modification to the `exclude` property.
 - Removed `BoundColumns._spawn_columns`.
 - `Table.data`, `Table.rows`, and `Table.columns` are now attributes
   rather than properties.
