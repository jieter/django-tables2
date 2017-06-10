from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse

try:
    from tablib import Dataset
except ImportError:
    raise ImproperlyConfigured(
        'You must have tablib installed in order to use the django-tables2 export functionality'
    )


class TableExport(object):
    CSV = 'csv'
    JSON = 'json'
    XLS = 'xls'
    XLSX = 'xlsx'
    YAML = 'yml'

    FORMATS = {
        CSV: 'text/csv; charset=utf-8',
        JSON: 'application/json;',
        XLS: 'application/vnd.ms-excel',
        XLSX: 'application/vnd.ms-excel',
        YAML: 'text/yml; charset=utf-8',
    }

    def __init__(self, export_format, table):
        self.format = export_format

        self.dataset = Dataset()
        for i, row in enumerate(table.as_values()):
            if i == 0:
                self.dataset.headers = row
            else:
                self.dataset.append(row)

    def content_type(self):
        return self.FORMATS[self.format]

    def export(self):
        if self.format == self.CSV:
            return self.dataset.csv
        elif self.format == self.JSON:
            return self.dataset.json
        elif self.format == self.XLS:
            return self.dataset.xls
        elif self.format == self.XLSX:
            return self.dataset.xlsx
        elif self.format == self.YAML:
            return self.dataset.yaml

    def response(self, filename):
        response = HttpResponse(content_type=self.content_type())
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            filename
        )

        response.write(self.export())
        return response
