from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse

if TYPE_CHECKING:
    from ..tables import Table

try:
    from tablib import Dataset
except ImportError:  # pragma: no cover
    raise ImproperlyConfigured(
        "You must have tablib installed in order to use the django-tables2 export functionality"
    )


class TableExport:
    """
    Export data from a table to the file type specified.

    Arguments:
        export_format (str): one of `csv, json, latex, ods, tsv, xls, xlsx, yaml`

        table (`~.Table`): instance of the table to export the data from

        exclude_columns (iterable): list of column names to exclude from the export

        dataset_kwargs (dictionary): passed as `**kwargs` to `tablib.Dataset` constructor

    """

    CSV = "csv"
    JSON = "json"
    LATEX = "latex"
    ODS = "ods"
    TSV = "tsv"
    XLS = "xls"
    XLSX = "xlsx"
    YAML = "yaml"

    FORMATS = {
        CSV: "text/csv; charset=utf-8",
        JSON: "application/json",
        LATEX: "text/plain",
        ODS: "application/vnd.oasis.opendocument.spreadsheet",
        TSV: "text/tsv; charset=utf-8",
        XLS: "application/vnd.ms-excel",
        XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        YAML: "text/yaml; charset=utf-8",
    }

    def __init__(
        self,
        export_format: str,
        table: "Table",
        exclude_columns: Iterable[str] | None = None,
        dataset_kwargs: dict[str, Any] | None = None,
    ):
        if not self.is_valid_format(export_format):
            raise TypeError(f'Export format "{export_format}" is not supported.')

        self.format = export_format
        self.dataset = self.table_to_dataset(table, exclude_columns, dataset_kwargs)

    def table_to_dataset(
        self,
        table: "Table",
        exclude_columns: Iterable[str] | None,
        dataset_kwargs: dict[str, Any] | None = None,
    ) -> Dataset:
        """Transform a table to a tablib dataset."""
        if not table.Meta.model:
            raise ImproperlyConfigured("table_to_dataset() requires a table based on a model.")

        try:
            title = table.Meta.model._meta.verbose_name_plural.title()
        except AttributeError:
            title = "Export Data"

        dataset = Dataset(title=title, **dataset_kwargs)
        for i, row in enumerate(table.as_values(exclude_columns=exclude_columns)):
            if i == 0:
                dataset.headers = row
            else:
                dataset.append(row)
        return dataset

    @classmethod
    def is_valid_format(self, export_format: str) -> bool:
        """Return True if `export_format` is one of the supported export formats."""
        return export_format is not None and export_format in TableExport.FORMATS

    def content_type(self) -> str:
        """Return the content type for the current export format."""
        return self.FORMATS[self.format]

    def export(self) -> str | bytes:
        """Return the string/bytes for the current export format."""
        return self.dataset.export(self.format)

    def response(self, filename: str | None = None) -> HttpResponse:
        """
        Build and return a `HttpResponse` containing the exported data.

        Arguments:
            filename (str): if not `None`, the filename is attached to the
                `Content-Disposition` header of the response.
        """
        response = HttpResponse(content_type=self.content_type())
        if filename is not None:
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

        response.write(self.export())
        return response
