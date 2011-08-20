# -*- coding: utf-8 -*-
import django_tables2 as tables


class CountryTable(tables.Table):
    name = tables.Column()
    population = tables.Column()
    tz = tables.Column(verbose_name='Time Zone')
    visits = tables.Column()


class ThemedCountryTable(CountryTable):
    class Meta:
        attrs = {'class': 'paleblue'}
