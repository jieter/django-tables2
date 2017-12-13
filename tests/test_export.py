# coding: utf-8
from __future__ import unicode_literals

import json
from unittest import skipIf

from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from django.test import TestCase

import django_tables2 as tables
from django_tables2.config import RequestConfig

from .app.models import Occupation, Person, Region
from .test_views import DispatchHookMixin
from .utils import build_request

try:
    from django_tables2.export.export import TableExport
    from django_tables2.export.views import ExportMixin
except ImproperlyConfigured:
    TableExport = None


NAMES = [
    ('Yildiz', 'van der Kuil'),
    ('Lindi', 'Hakvoort'),
    ('Gerardo', 'Castelein'),
]

EXPECTED_CSV = '\r\n'.join(
    ('First Name,Surname', ) + tuple(','.join(name) for name in NAMES)
) + '\r\n'

EXPECTED_JSON = list([
    {'First Name': first_name, 'Surname': last_name}
    for first_name, last_name in NAMES
])


class Table(tables.Table):
    first_name = tables.Column()
    last_name = tables.Column()


class View(DispatchHookMixin, ExportMixin, tables.SingleTableView):
    table_class = Table
    table_pagination = {'per_page': 1}
    model = Person  # required for ListView
    template_name = 'django_tables2/bootstrap.html'


@skipIf(TableExport is None, 'Tablib is required to run the export tests')
class ExportViewTest(TestCase):
    def setUp(self):
        for first_name, last_name in NAMES:
            Person.objects.create(first_name=first_name, last_name=last_name)

    def test_view_should_support_csv_export(self):
        response, view = View.as_view()(build_request('/?_export=csv'))
        assert response.getvalue().decode('utf8') == EXPECTED_CSV

        # should just render the normal table without the _export query
        response, view = View.as_view()(build_request('/'))
        html = response.render().rendered_content

        assert 'Yildiz' in html
        assert 'Lindy' not in html

    def test_should_raise_error_for_unsupported_file_type(self):
        table = Table([])

        with self.assertRaises(TypeError):
            TableExport(table=table, export_format='exe')

    def test_should_support_json_export(self):
        response, view = View.as_view()(build_request('/?_export=json'))
        assert json.loads(response.getvalue().decode('utf8')) == EXPECTED_JSON

    def test_should_support_custom_trigger_param(self):
        class View(DispatchHookMixin, ExportMixin, tables.SingleTableView):
            table_class = Table
            export_trigger_param = 'export_to'
            model = Person  # required for ListView

        response, view = View.as_view()(build_request('/?export_to=json'))
        assert json.loads(response.getvalue().decode('utf8')) == EXPECTED_JSON

    def test_should_support_custom_filename(self):
        class View(DispatchHookMixin, ExportMixin, tables.SingleTableView):
            table_class = Table
            export_name = 'people'
            model = Person  # required for ListView

        response, view = View.as_view()(build_request('/?_export=json'))
        assert response['Content-Disposition'] == 'attachment; filename="people.json"'

    def test_function_view(self):
        '''
        Test the code used in the docs
        '''
        def table_view(request):
            table = Table(Person.objects.all())
            RequestConfig(request).configure(table)

            export_format = request.GET.get('_export', None)
            if TableExport.is_valid_format(export_format):
                exporter = TableExport(export_format, table)
                return exporter.response('table.{}'.format(export_format))

            return render(request, 'django_tables2/table.html', {
                'table': table
            })

        response = table_view(build_request('/?_export=csv'))
        assert response.getvalue().decode('utf8') == EXPECTED_CSV

        # must also support the normal html table.
        response = table_view(build_request('/'))
        html = response.content.decode('utf8')

        assert 'Yildiz' in html
        assert 'Lindy' not in html


class OccupationTable(tables.Table):
    name = tables.Column()
    boolean = tables.Column()
    region = tables.Column()


class OccupationView(DispatchHookMixin, ExportMixin, tables.SingleTableView):
    table_class = OccupationTable
    table_pagination = {'per_page': 1}
    model = Occupation
    template_name = 'django_tables2/bootstrap.html'


@skipIf(TableExport is None, 'Tablib is required to run the export tests')
class AdvancedExportViewTest(TestCase):
    def setUp(self):
        richard = Person.objects.create(first_name='Richard', last_name='Queener')

        vlaanderen = Region.objects.create(name='Vlaanderen', mayor=richard)
        Occupation.objects.create(name='Timmerman', boolean=True, region=vlaanderen)
        Occupation.objects.create(name='Ecoloog', boolean=False, region=vlaanderen)

    def test_should_work_with_foreign_keys(self):
        response, view = OccupationView.as_view()(build_request('/?_export=xls'))
        data = response.content
        # binary data, so not possible to compare to an exact expectation
        assert data.find('Vlaanderen'.encode())
        assert data.find('Ecoloog'.encode())
        assert data.find('Timmerman'.encode())

    def test_should_work_with_foreign_key_fields(self):
        class OccupationWithForeignKeyFieldsTable(tables.Table):
            name = tables.Column()
            boolean = tables.Column()
            region = tables.Column()
            mayor = tables.Column(accessor='region.mayor.first_name')

        class View(DispatchHookMixin, ExportMixin, tables.SingleTableView):
            table_class = OccupationWithForeignKeyFieldsTable
            table_pagination = {'per_page': 1}
            model = Occupation
            template_name = 'django_tables2/bootstrap.html'

        response, view = View.as_view()(build_request('/?_export=csv'))
        data = response.getvalue().decode('utf8')

        expected_csv = '\r\n'.join((
            'Name,Boolean,Region,First Name',
            'Timmerman,True,Vlaanderen,Richard',
            'Ecoloog,False,Vlaanderen,Richard\r\n'
        ))
        assert data == expected_csv

    def test_should_allow_exclude_columns(self):
        class OccupationExcludingView(DispatchHookMixin, ExportMixin, tables.SingleTableView):
            table_class = OccupationTable
            table_pagination = {'per_page': 1}
            model = Occupation
            template_name = 'django_tables2/bootstrap.html'
            exclude_columns = ('boolean', )

        response, view = OccupationExcludingView.as_view()(build_request('/?_export=csv'))
        data = response.getvalue().decode('utf8')

        assert data.splitlines()[0] == 'Name,Region'


@skipIf(TableExport is None, 'Tablib is required to run the export tests')
class UnicodeExportViewTest(TestCase):
    def test_exporting_unicode_data(self):
        unicode_name = '木匠'
        Occupation.objects.create(name=unicode_name)

        expected_csv = 'Name,Boolean,Region\r\n{},,\r\n'.format(unicode_name)

        response, view = OccupationView.as_view()(build_request('/?_export=csv'))
        assert response.getvalue().decode('utf8') == expected_csv

        # smoke tests, hard to test this binary format for string containment
        response, view = OccupationView.as_view()(build_request('/?_export=xls'))
        data = response.content
        assert len(data) > len(expected_csv)

        response, view = OccupationView.as_view()(build_request('/?_export=xlsx'))
        data = response.content
        assert len(data) > len(expected_csv)

    def test_exporting_unicode_header(self):
        unicode_header = 'hé'

        class Table(tables.Table):
            name = tables.Column(verbose_name=unicode_header)

        exporter = TableExport('csv', Table([]))
        response = exporter.response()
        assert response.getvalue().decode('utf8') == unicode_header + '\r\n'

        exporter = TableExport('xls', Table([]))
        # this would fail if the header contains unicode and string converstion is attempted.
        exporter.export()
