from __future__ import unicode_literals

from .export import TableExport


class ExportMixin(object):
    '''
    Support various export formats for the table data.

    `ExportMixin` looks for some attributes on the class to change it's behaviour:

    Attributes:
        export_name (str): is the name of file that will be exported, without extension.
        export_trigger_param (str): is the name of the GET attribute used to trigger
            the export. It's value decides the export format, refer to
            `TableExport` for a list of available formats.
        exclude_columns (iterable): column names excluded from the export.
            For example, one might want to exclude columns containing buttons from
            the export. Excluding columns from the export is also possible using the
            `exclude_from_export` argument to the `.Column` constructor::

                class Table(tables.Table):
                    name = tables.Column()
                    buttons = tables.TemplateColumn(exclude_from_export=True, template_name=...)
    '''
    export_name = 'table'
    export_trigger_param = '_export'
    exclude_columns = ()

    def get_export_filename(self, export_format):
        return '{}.{}'.format(self.export_name, export_format)

    def create_export(self, export_format):
        exporter = TableExport(
            export_format=export_format,
            table=self.get_table(**self.get_table_kwargs()),
            exclude_columns=self.exclude_columns
        )

        return exporter.response(filename=self.get_export_filename(export_format))

    def render_to_response(self, context, **kwargs):
        export_format = self.request.GET.get(self.export_trigger_param, None)
        if TableExport.is_valid_format(export_format):
            return self.create_export(export_format)

        return super(ExportMixin, self).render_to_response(context, **kwargs)
