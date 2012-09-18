# coding: utf-8
# pylint: disable=R0912,E0102
from __future__ import unicode_literals
from attest import assert_hook, Tests, warns  # pylint: disable=W0611
from datetime import date, datetime
from django_attest import settings, TestContext
import django_tables2 as tables
from django_tables2.utils import build_request
from django_tables2 import A, Attrs
from django.db import models
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.utils.translation import ugettext
from django.utils.safestring import mark_safe, SafeData
try:
    from django.utils import timezone
except ImportError:
    timezone = None
import pytz
from .app.models import Person
from .templates import attrs, parse


booleancolumn = Tests()


@booleancolumn.test
def should_be_used_for_booleanfield():
    class BoolModel(models.Model):
        field = models.BooleanField()

    class Table(tables.Table):
        class Meta:
            model = BoolModel

    column = Table.base_columns["field"]
    assert type(column) == tables.BooleanColumn
    assert column.empty_values != ()


@booleancolumn.test
def should_be_used_for_nullbooleanfield():
    class NullBoolModel(models.Model):
        field = models.NullBooleanField()

    class Table(tables.Table):
        class Meta:
            model = NullBoolModel

    column = Table.base_columns["field"]
    assert type(column) == tables.BooleanColumn
    assert column.empty_values == ()


@booleancolumn.test
def treat_none_different_from_false():
    class Table(tables.Table):
        col = tables.BooleanColumn(null=False, default="---")

    table = Table([{"col": None}])
    assert table.rows[0]["col"] == "---"


@booleancolumn.test
def treat_none_as_false():
    class Table(tables.Table):
        col = tables.BooleanColumn(null=True)

    table = Table([{"col": None}])
    assert table.rows[0]["col"] == '<span class="false">✘</span>'


@booleancolumn.test
def span_attrs():
    class Table(tables.Table):
        col = tables.BooleanColumn(attrs={"span": {"key": "value"}})

    table = Table([{"col": True}])
    assert table.rows[0]["col"] == '<span class="true" key="value">✔</span>'


checkboxcolumn = Tests()


@checkboxcolumn.test
def attrs_should_be_translated_for_backwards_compatibility():
    with warns(DeprecationWarning):
        class TestTable(tables.Table):
            col = tables.CheckBoxColumn(header_attrs={"th_key": "th_value"},
                                        attrs={"td_key": "td_value"})

    table = TestTable([{"col": "data"}])
    assert attrs(table.columns["col"].header) == {"type": "checkbox", "th_key": "th_value"}
    assert attrs(table.rows[0]["col"])        == {"type": "checkbox", "td_key": "td_value", "value": "data", "name": "col"}


@checkboxcolumn.test
def new_attrs_should_be_supported():
    class TestTable(tables.Table):
        col1 = tables.CheckBoxColumn(attrs=Attrs(th__input={"th_key": "th_value"},
                                                 td__input={"td_key": "td_value"}))
        col2 = tables.CheckBoxColumn(attrs=Attrs(input={"key": "value"}))

    table = TestTable([{"col1": "data", "col2": "data"}])
    assert attrs(table.columns["col1"].header) == {"type": "checkbox", "th_key": "th_value"}
    assert attrs(table.rows[0]["col1"])        == {"type": "checkbox", "td_key": "td_value", "value": "data", "name": "col1"}
    assert attrs(table.columns["col2"].header) == {"type": "checkbox", "key": "value"}
    assert attrs(table.rows[0]["col2"])        == {"type": "checkbox", "key": "value", "value": "data", "name": "col2"}


general = Tests()


@general.test
def column_header_should_use_titlised_verbose_name():
    class SimpleTable(tables.Table):
        basic = tables.Column()
        acronym = tables.Column(verbose_name="has FBI help")

    table = SimpleTable([])
    assert table.columns["basic"].header == "Basic"
    assert table.columns["acronym"].header == "Has FBI Help"


@general.test
def should_support_safe_verbose_name():
    class SimpleTable(tables.Table):
        safe = tables.Column(verbose_name=mark_safe("<b>Safe</b>"))

    table = SimpleTable([])
    assert isinstance(table.columns["safe"].header, SafeData)


@general.test
def should_support_safe_verbose_name_via_model():
    class PersonTable(tables.Table):
        safe = tables.Column()

    table = PersonTable(Person.objects.all())
    assert isinstance(table.columns["safe"].header, SafeData)


@general.test
def sortable_backwards_compatibility():
    # Table.Meta.sortable (not set)
    class SimpleTable(tables.Table):
        name = tables.Column()
    table = SimpleTable([])
    with warns(DeprecationWarning):
        assert table.columns['name'].sortable is True

    # Table.Meta.sortable = False
    with warns(DeprecationWarning):
        class SimpleTable(tables.Table):
            name = tables.Column()

            class Meta:
                sortable = False
    table = SimpleTable([])
    with warns(DeprecationWarning):
        assert table.columns['name'].sortable is False  # backwards compatible
    assert table.columns['name'].orderable is False

    # Table.Meta.sortable = True
    with warns(DeprecationWarning):
        class SimpleTable(tables.Table):
            name = tables.Column()

            class Meta:
                sortable = True
    table = SimpleTable([])
    with warns(DeprecationWarning):
        assert table.columns['name'].sortable is True  # backwards compatible
    assert table.columns['name'].orderable is True


@general.test
def orderable():
    # Table.Meta.orderable = False
    class SimpleTable(tables.Table):
        name = tables.Column()
    table = SimpleTable([])
    assert table.columns['name'].orderable is True

    # Table.Meta.orderable = False
    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            orderable = False
    table = SimpleTable([])
    assert table.columns['name'].orderable is False
    with warns(DeprecationWarning):
        assert table.columns['name'].sortable is False  # backwards compatible

    # Table.Meta.orderable = True
    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            orderable = True
    table = SimpleTable([])
    with warns(DeprecationWarning):
        assert table.columns['name'].sortable is True  # backwards compatible
    assert table.columns['name'].orderable is True


@general.test
def order_by_defaults_to_accessor():
    class SimpleTable(tables.Table):
        foo = tables.Column(accessor="bar")

    table = SimpleTable([])
    assert table.columns["foo"].order_by == ("bar", )


@general.test
def supports_order_by():
    class SimpleTable(tables.Table):
        name = tables.Column(order_by=("last_name", "-first_name"))
        age = tables.Column()

    table = SimpleTable([], order_by=("-age", ))
    # alias
    assert table.columns["name"].order_by_alias == "name"
    assert table.columns["age"].order_by_alias == "-age"
    # order by
    assert table.columns["name"].order_by == ("last_name", "-first_name")
    assert table.columns["age"].order_by == ("-age", )

    # now try with name ordered
    table = SimpleTable([], order_by=("-name", ))
    # alias
    assert table.columns["name"].order_by_alias == "-name"
    assert table.columns["age"].order_by_alias == "age"
    # alias next
    assert table.columns["name"].order_by_alias.next == "name"
    assert table.columns["age"].order_by_alias.next == "age"
    # order by
    assert table.columns["name"].order_by == ("-last_name", "first_name")
    assert table.columns["age"].order_by == ("age", )


@general.test
def supports_is_ordered():
    class SimpleTable(tables.Table):
        name = tables.Column()

    # sorted
    table = SimpleTable([], order_by='name')
    assert table.columns["name"].is_ordered
    # unsorted
    table = SimpleTable([])
    assert not table.columns["name"].is_ordered


@general.test
def translation():
    """
    Tests different types of values for the ``verbose_name`` property of a
    column.
    """
    class TranslationTable(tables.Table):
        normal = tables.Column(verbose_name=ugettext("Normal"))
        lazy = tables.Column(verbose_name=ugettext("Lazy"))

    table = TranslationTable([])
    assert "Normal" == table.columns["normal"].header
    assert "Lazy" == table.columns["lazy"].header


@general.test
def sequence():
    """
    Ensures that the sequence of columns is configurable.
    """
    class TestTable(tables.Table):
        a = tables.Column()
        b = tables.Column()
        c = tables.Column()
    assert ["a", "b", "c"] == TestTable([]).columns.names()
    assert ["b", "a", "c"] == TestTable([], sequence=("b", "a", "c")).columns.names()

    class TestTable2(TestTable):
        class Meta:
            sequence = ("b", "a", "c")
    assert ["b", "a", "c"] == TestTable2([]).columns.names()
    assert ["a", "b", "c"] == TestTable2([], sequence=("a", "b", "c")).columns.names()

    class TestTable3(TestTable):
        class Meta:
            sequence = ("c", )
    assert ["c", "a", "b"] == TestTable3([]).columns.names()
    assert ["c", "a", "b"] == TestTable([], sequence=("c", )).columns.names()

    class TestTable4(TestTable):
        class Meta:
            sequence = ("...", )
    assert ["a", "b", "c"] == TestTable4([]).columns.names()
    assert ["a", "b", "c"] == TestTable([], sequence=("...", )).columns.names()

    class TestTable5(TestTable):
        class Meta:
            sequence = ("b", "...")
    assert ["b", "a", "c"] == TestTable5([]).columns.names()
    assert ["b", "a", "c"] == TestTable([], sequence=("b", "...")).columns.names()

    class TestTable6(TestTable):
        class Meta:
            sequence = ("...", "b")
    assert ["a", "c", "b"] == TestTable6([]).columns.names()
    assert ["a", "c", "b"] == TestTable([], sequence=("...", "b")).columns.names()

    class TestTable7(TestTable):
        class Meta:
            sequence = ("b", "...", "a")
    assert ["b", "c", "a"] == TestTable7([]).columns.names()
    assert ["b", "c", "a"] == TestTable([], sequence=("b", "...", "a")).columns.names()

    # Let's test inheritence
    class TestTable8(TestTable):
        d = tables.Column()
        e = tables.Column()
        f = tables.Column()

        class Meta:
            sequence = ("d", "...")

    class TestTable9(TestTable):
        d = tables.Column()
        e = tables.Column()
        f = tables.Column()

    assert ["d", "a", "b", "c", "e", "f"] == TestTable8([]).columns.names()
    assert ["d", "a", "b", "c", "e", "f"] == TestTable9([], sequence=("d", "...")).columns.names()


@general.test
def should_support_both_meta_sequence_and_constructor_exclude():
    """
    Issue #32 describes a problem when both ``Meta.sequence`` and
    ``Table(..., exclude=...)`` are used on a single table. The bug caused an
    exception to be raised when the table was iterated.
    """
    class SequencedTable(tables.Table):
        a = tables.Column()
        b = tables.Column()
        c = tables.Column()

        class Meta:
            sequence = ('a', '...')

    table = SequencedTable([], exclude=('c', ))
    table.as_html()


@general.test
def bound_columns_should_support_indexing():
    class SimpleTable(tables.Table):
        a = tables.Column()
        b = tables.Column()

    table = SimpleTable([])
    assert 'b' == table.columns[1].name
    assert 'b' == table.columns['b'].name


@general.test
def cell_attrs_applies_to_td_and_th():
    class SimpleTable(tables.Table):
        a = tables.Column(attrs=Attrs(cell={"key": "value"}))

    # providing data ensures 1 row is rendered
    table = SimpleTable([{"a": "value"}])
    root = parse(table.as_html())

    assert root.findall('.//thead/tr/th')[0].attrib == {"key": "value", "class": "a orderable sortable"}
    assert root.findall('.//tbody/tr/td')[0].attrib == {"key": "value", "class": "a"}


@general.test
def cells_are_automatically_given_column_name_as_class():
    class SimpleTable(tables.Table):
        a = tables.Column()

    table = SimpleTable([{"a": "value"}])
    root = parse(table.as_html())
    assert root.findall('.//thead/tr/th')[0].attrib == {"class": "a orderable sortable"}
    assert root.findall('.//tbody/tr/td')[0].attrib == {"class": "a"}


@general.test
def th_are_given_sortable_class_if_column_is_orderable():
    class SimpleTable(tables.Table):
        a = tables.Column()
        b = tables.Column(orderable=False)

    table = SimpleTable([{"a": "value"}])
    root = parse(table.as_html())
    # return classes of an element as a set
    classes = lambda x: set(x.attrib["class"].split())
    assert "sortable" in classes(root.findall('.//thead/tr/th')[0])
    assert "sortable" not in classes(root.findall('.//thead/tr/th')[1])

    # Now try with an ordered table
    table = SimpleTable([], order_by="a")
    root = parse(table.as_html())
    # return classes of an element as a set
    assert "sortable" in classes(root.findall('.//thead/tr/th')[0])
    assert "asc" in classes(root.findall('.//thead/tr/th')[0])
    assert "sortable" not in classes(root.findall('.//thead/tr/th')[1])


@general.test
def empty_values_triggers_default():
    class Table(tables.Table):
        a = tables.Column(empty_values=(1, 2), default="--")

    table = Table([{"a": 1}, {"a": 2}, {"a": 3}, {"a": 4}])
    assert [x["a"] for x in table.rows] == ["--", "--", 3, 4]


linkcolumn = Tests()
linkcolumn.context(TestContext())

@linkcolumn.test
def unicode():
    """Test LinkColumn"""
    # test unicode values + headings
    class UnicodeTable(tables.Table):
        first_name = tables.LinkColumn('person', args=[A('pk')])
        last_name = tables.LinkColumn('person', args=[A('pk')], verbose_name=u'äÚ¨´ˆÁ˜¨ˆ˜˘Ú…Ò˚ˆπ∆ˆ´')

    dataset = [
        {'pk': 1, 'first_name': u'Brädley', 'last_name': u'∆yers'},
        {'pk': 2, 'first_name': u'Chr…s', 'last_name': u'DÒble'},
    ]

    table = UnicodeTable(dataset)
    request = build_request('/some-url/')
    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': request, 'table': table}))

    assert u'Brädley' in html
    assert u'∆yers' in html
    assert u'Chr…s' in html
    assert u'DÒble' in html


@linkcolumn.test
def null_foreign_key():
    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()
        occupation = tables.LinkColumn('occupation', args=[A('occupation.pk')])

    Person.objects.create(first_name='bradley', last_name='ayers')

    table = PersonTable(Person.objects.all())
    table.as_html()


@linkcolumn.test
def kwargs():
    class PersonTable(tables.Table):
        a = tables.LinkColumn('occupation', kwargs={"pk": A('a')})

    html = PersonTable([{"a": 0}, {"a": 1}]).as_html()
    assert reverse("occupation", kwargs={"pk": 0}) in html
    assert reverse("occupation", kwargs={"pk": 1}) in html


@linkcolumn.test
def html_escape_value():
    class PersonTable(tables.Table):
        name = tables.LinkColumn("escaping", kwargs={"pk": A("pk")})

    table = PersonTable([{"name": "<brad>", "pk": 1}])
    assert table.rows[0]["name"] == '<a href="/&amp;&#39;%22/1/">&lt;brad&gt;</a>'


@linkcolumn.test
def old_style_attrs_should_still_work():
    with warns(DeprecationWarning):
        class TestTable(tables.Table):
            col = tables.LinkColumn('occupation', kwargs={"pk": A('col')},
                                    attrs={"title": "Occupation Title"})

    table = TestTable([{"col": 0}])
    assert attrs(table.rows[0]["col"]) == {"href": reverse("occupation", kwargs={"pk": 0}),
                                           "title": "Occupation Title"}


@linkcolumn.test
def a_attrs_should_be_supported():
    class TestTable(tables.Table):
        col = tables.LinkColumn('occupation', kwargs={"pk": A('col')},
                                attrs=Attrs(a={"title": "Occupation Title"}))

    table = TestTable([{"col": 0}])
    assert attrs(table.rows[0]["col"]) == {"href": reverse("occupation", kwargs={"pk": 0}),
                                           "title": "Occupation Title"}


@linkcolumn.test
def defaults():
    class Table(tables.Table):
        link = tables.LinkColumn('occupation', kwargs={"pk": 1}, default="xyz")

    table = Table([{}])
    assert table.rows[0]['link'] == 'xyz'


templatecolumn = Tests()


@templatecolumn.test
def should_handle_context_on_table():
    class TestTable(tables.Table):
        col_code = tables.TemplateColumn(template_code="code:{{ record.col }}{{ STATIC_URL }}")
        col_name = tables.TemplateColumn(template_name="test_template_column.html")

    table = TestTable([{"col": "brad"}])
    assert table.rows[0]["col_code"] == "code:brad"
    assert table.rows[0]["col_name"] == "name:brad"
    table.context = Context({"STATIC_URL": "/static/"})
    assert table.rows[0]["col_code"] == "code:brad/static/"
    assert table.rows[0]["col_name"] == "name:brad/static/"


@templatecolumn.test
def should_support_default():
    class Table(tables.Table):
        foo = tables.TemplateColumn("default={{ default }}", default="bar")

    table = Table([{}])
    assert table.rows[0]["foo"] == "default=bar"


@templatecolumn.test
def should_support_value():
    class Table(tables.Table):
        foo = tables.TemplateColumn("value={{ value }}")

    table = Table([{"foo": "bar"}])
    assert table.rows[0]["foo"] == "value=bar"


urlcolumn = Tests()


@urlcolumn.test
def should_turn_url_into_hyperlink():
    class TestTable(tables.Table):
        url = tables.URLColumn()

    table = TestTable([{"url": "http://example.com"}])
    assert table.rows[0]["url"] == '<a href="http://example.com">http://example.com</a>'


@urlcolumn.test
def should_be_used_for_urlfields():
    class URLModel(models.Model):
        field = models.URLField()

    class Table(tables.Table):
        class Meta:
            model = URLModel

    assert type(Table.base_columns["field"]) == tables.URLColumn


emailcolumn = Tests()


@emailcolumn.test
def should_turn_email_address_into_hyperlink():
    class Table(tables.Table):
        email = tables.EmailColumn()

    table = Table([{"email": "test@example.com"}])
    assert table.rows[0]["email"] == '<a href="mailto:test@example.com">test@example.com</a>'


@emailcolumn.test
def should_render_default_for_blank():
    class Table(tables.Table):
        email = tables.EmailColumn(default="---")

    table = Table([{"email": ""}])
    assert table.rows[0]["email"] == '---'


@emailcolumn.test
def should_be_used_for_datetimefields():
    class EmailModel(models.Model):
        field = models.EmailField()

    class Table(tables.Table):
        class Meta:
            model = EmailModel

    assert type(Table.base_columns["field"]) == tables.EmailColumn


datecolumn = Tests()

# Format string: https://docs.djangoproject.com/en/1.4/ref/templates/builtins/#date
# D -- Day of the week, textual, 3 letters  -- 'Fri'
# b -- Month, textual, 3 letters, lowercase -- 'jan'
# Y -- Year, 4 digits.                      -- '1999'

@datecolumn.test
def should_handle_explicit_format():
    class TestTable(tables.Table):
        date = tables.DateColumn(format="D b Y")

        class Meta:
            default = "—"

    table = TestTable([{"date": date(2012, 9, 11)},
                       {"date": None}])
    assert table.rows[0]["date"] == "Tue sep 2012"
    assert table.rows[1]["date"] == "—"


@datecolumn.test
def should_handle_long_format():
    with settings(DATE_FORMAT="D Y b"):
        class TestTable(tables.Table):
            date = tables.DateColumn(short=False)

            class Meta:
                default = "—"

        table = TestTable([{"date": date(2012, 9, 11)},
                           {"date": None}])
        assert table.rows[0]["date"] == "Tue 2012 sep"
        assert table.rows[1]["date"] == "—"


@datecolumn.test
def should_handle_short_format():
    with settings(SHORT_DATE_FORMAT="b Y D"):
        class TestTable(tables.Table):
            date = tables.DateColumn(short=True)

            class Meta:
                default = "—"

        table = TestTable([{"date": date(2012, 9, 11)},
                           {"date": None}])
        assert table.rows[0]["date"] == "sep 2012 Tue"
        assert table.rows[1]["date"] == "—"


@datecolumn.test
def should_be_used_for_datefields():
    class DateModel(models.Model):
        field = models.DateField()

    class Table(tables.Table):
        class Meta:
            model = DateModel

    assert type(Table.base_columns["field"]) == tables.DateColumn


datetimecolumn = Tests()

# Format string: https://docs.djangoproject.com/en/1.4/ref/templates/builtins/#date
# D -- Day of the week, textual, 3 letters  -- 'Fri'
# b -- Month, textual, 3 letters, lowercase -- 'jan'
# Y -- Year, 4 digits.                      -- '1999'
# A -- 'AM' or 'PM'.                        -- 'AM'
# f -- Time, in 12-hour hours[:minutes]     -- '1', '1:30'


@datetimecolumn.context
def dt():
    dt = datetime(2012, 9, 11, 12, 30)
    if timezone:
        # If the version of Django has timezone support, convert from naive to
        # UTC, the test project uses Australia/Brisbane so regardless the
        # output from the column should be the same.
        dt = (dt.replace(tzinfo=pytz.timezone("Australia/Brisbane"))
                .astimezone(pytz.UTC))
    yield dt


@datetimecolumn.test
def should_handle_explicit_format(dt):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(format="D b Y")

        class Meta:
            default = "—"

    table = TestTable([{"date": dt}, {"date": None}])
    assert table.rows[0]["date"] == "Tue sep 2012"
    assert table.rows[1]["date"] == "—"


@datetimecolumn.test
def should_handle_long_format(dt):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(short=False)

        class Meta:
            default = "—"

    with settings(DATETIME_FORMAT="D Y b A f"):
        table = TestTable([{"date": dt}, {"date": None}])
        assert table.rows[0]["date"] == "Tue 2012 sep PM 12:30"
        assert table.rows[1]["date"] == "—"


@datetimecolumn.test
def should_handle_short_format(dt):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(short=True)

        class Meta:
            default = "—"

    with settings(SHORT_DATETIME_FORMAT="b Y D A f"):
        table = TestTable([{"date": dt}, {"date": None}])
        assert table.rows[0]["date"] == "sep 2012 Tue PM 12:30"
        assert table.rows[1]["date"] == "—"


@datetimecolumn.test
def should_be_used_for_datetimefields():
    class DateTimeModel(models.Model):
        field = models.DateTimeField()

    class Table(tables.Table):
        class Meta:
            model = DateTimeModel

    assert type(Table.base_columns["field"]) == tables.DateTimeColumn


columns = Tests([booleancolumn, checkboxcolumn, datecolumn, datetimecolumn,
                 emailcolumn, general, linkcolumn, templatecolumn, urlcolumn])
