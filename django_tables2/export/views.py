from __future__ import unicode_literals

from .export import TableExport


class ExportMixin(object):
    '''
    Support various export formats for the table data.
    '''
    export_trigger_param = '_export'

    def get_export_filename(self, export_format):
        return 'table.{}'.format(export_format)

    def create_export(self, export_format):
        exporter = TableExport(
            export_format=export_format,
            table=self.get_table(**self.get_table_kwargs())
        )

        return exporter.response(filename=self.get_export_filename(export_format))

    def render_to_response(self, context, **kwargs):
        export_format = self.request.GET.get(self.export_trigger_param, None)
        if TableExport.is_valid_format(export_format):
            return self.create_export(export_format)

        return super(ExportMixin, self).render_to_response(context, **kwargs)
