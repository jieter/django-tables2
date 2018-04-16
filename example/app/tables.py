# coding: utf-8
import django_tables2 as tables

from .models import Country, Person


class CountryTable(tables.Table):
    name = tables.Column()
    population = tables.Column()
    tz = tables.Column(verbose_name='time zone')
    visits = tables.Column()
    summary = tables.Column(order_by=('name', 'population'))

    class Meta:
        model = Country


class ThemedCountryTable(CountryTable):
    class Meta:
        attrs = {'class': 'paleblue'}


class BootstrapTable(tables.Table):

    country = tables.RelatedLinkColumn()

    class Meta:
        model = Person
        template_name = 'django_tables2/bootstrap.html'
        exclude = ('friendly', )


class BootstrapTablePinnedRows(BootstrapTable):

    class Meta(BootstrapTable.Meta):
        pinned_row_attrs = {
            'class': 'info'
        }

    def get_top_pinned_data(self):
        return [
            {'name': 'Most used country: ', 'country': Country.objects.filter(name='Cameroon').first()}
        ]


class Bootstrap4Table(tables.Table):
    country = tables.RelatedLinkColumn()
    # continent = tables.RelatedLinkColumn(accessor='country.continent')

    class Meta:
        model = Person
        template_name = 'django_tables2/bootstrap4.html'
        attrs = {'class': 'table table-hover'}
        exclude = ('friendly', )


class SemanticTable(tables.Table):

    country = tables.RelatedLinkColumn()

    class Meta:
        model = Person
        template_name = 'django_tables2/semantic.html'
        exclude = ('friendly', )


class PersonTable(tables.Table):
    country = tables.RelatedLinkColumn()

    class Meta:
        model = Person
        template_name = 'django_tables2/bootstrap.html'
