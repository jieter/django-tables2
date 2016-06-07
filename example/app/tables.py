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
        template = 'django_tables2/bootstrap.html'


class PersonTable(tables.Table):

    class Meta:
        model = Person
        template = 'django_tables2/bootstrap.html'
