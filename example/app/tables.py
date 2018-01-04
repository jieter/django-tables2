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
        attrs = {'class': 'table table-bordered table-striped table-hover'}
        exclude = ('friendly', )


class Bootstrap4Table(tables.Table):
    country = tables.RelatedLinkColumn()

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
        # attrs = {'class': 'ui table table-bordered table-striped table-hover'}
        exclude = ('friendly', )


class PersonTable(tables.Table):
    pagination_style = 'range'
    class Meta:
        model = Person
