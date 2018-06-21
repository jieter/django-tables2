from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse

try:
    from tablib import Dataset
except ImportError:  # pragma: no cover
    raise ImproperlyConfigured(
        "You must have tablib installed in order to use the django-tables2 export functionality"
    )


class TableExport(object):
    """
    Export data from a table to the file type specified.

    Arguments:
        export_format (str): one of `csv, json, latex, ods, tsv, xls, xlsx, yml`

        table (`~.Table`): instance of the table to export the data from

        exclude_columns (iterable): list of column names to exclude from the export
    """

    CSV = "csv"
    JSON = "json"
    LATEX = "latex"
    ODS = "ods"
    TSV = "tsv"
    XLS = "xls"
    XLSX = "xlsx"
    YAML = "yml"

    FORMATS = {
        CSV: "text/csv; charset=utf-8",
        JSON: "application/json",
        LATEX: "text/plain",
        ODS: "application/vnd.oasis.opendocument.spreadsheet",
        TSV: "text/tsv; charset=utf-8",
        XLS: "application/vnd.ms-excel",
        XLSX: "application/vnd.ms-excel",
        YAML: "text/yml; charset=utf-8",
    }

    def __init__(self, export_format, table, exclude_columns=None):
        if not self.is_valid_format(export_format):
            raise TypeError('Export format "{}" is not supported.'.format(export_format))

        self.format = export_format

        self.dataset = Dataset()
        for i, row in enumerate(table.as_values(exclude_columns=exclude_columns)):
            if i == 0:
                self.dataset.headers = row
            else:
                self.dataset.append(row)

    @classmethod
    def is_valid_format(self, export_format):
        """
        Returns true if `export_format` is one of the supported export formats
        """
        return export_format is not None and export_format in TableExport.FORMATS.keys()

    def content_type(self):
        """
        Returns the content type for the current export format
        """
        return self.FORMATS[self.format]

    def export(self):
        """
        Returns the string/bytes for the current export format
        """
        return getattr(self.dataset, self.format)

    def response(self, filename=None):
        """
        Builds and returns a `HttpResponse` containing the exported data

        Arguments:
            filename (str): if not `None`, the filename is attached to the
                `Content-Disposition` header of the response.
        """
        response = HttpResponse(content_type=self.content_type())
        if filename is not None:
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)

        response.write(self.export())
        return response
