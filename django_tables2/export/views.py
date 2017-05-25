from __future__ import unicode_literals

from django.http import HttpResponse

from tablib import Dataset


class ExportMixin(object):
    report_trigger_param = '_report'
    report_download_filename = 'table.csv'

    def create_export(self):
        table = self.get_table(**self.get_table_kwargs())

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            self.report_download_filename
        )
        data = table.as_values()

        dataset = Dataset()
        for i, row in enumerate(data):
            if i == 0:
                dataset.header = row
            else:
                dataset.append(row)

        response.write(dataset.csv)
        return response

    def render_to_response(self, context, **kwargs):
        if self.report_trigger_param in self.request.GET:
            return self.create_report()

        return super(ExportMixin, self).render_to_response(context, **kwargs)
