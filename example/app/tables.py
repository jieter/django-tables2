# coding: utf-8
from __future__ import unicode_literals

import django_tables2 as tables
from django_tables2 import A

from .models import Country, Person


class CountryTable(tables.Table):
    name = tables.Column()
    population = tables.Column()
    tz = tables.Column(verbose_name="time zone")
    visits = tables.Column()
    summary = tables.Column(order_by=("name", "population"))

    class Meta:
        model = Country


class ThemedCountryTable(CountryTable):
    class Meta:
        attrs = {"class": "paleblue"}


class CheckboxTable(tables.Table):
    select = tables.CheckBoxColumn(empty_values=(), footer="")

    population = tables.Column(attrs={"cell": {"class": "population"}})

    class Meta:
        model = Country
        template_name = "django_tables2/bootstrap.html"
        fields = ("select", "name", "population")


class BootstrapTable(tables.Table):
    id = tables.Column().linkify()
    country = tables.Column().linkify()
    continent = tables.Column(accessor="country.continent.name", verbose_name="Continent").linkify()

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap.html"
        exclude = ("friendly",)


class BootstrapTablePinnedRows(BootstrapTable):
    class Meta(BootstrapTable.Meta):
        pinned_row_attrs = {"class": "info"}

    def get_top_pinned_data(self):
        return [
            {
                "name": "Most used country: ",
                "country": Country.objects.filter(name="Cameroon").first(),
            }
        ]


class Bootstrap4Table(tables.Table):
    country = tables.Column().linkify()
    continent = tables.Column(accessor="country.continent").linkify()

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-hover"}
        exclude = ("friendly",)


class SemanticTable(tables.Table):

    country = tables.RelatedLinkColumn()

    class Meta:
        model = Person
        template_name = "django_tables2/semantic.html"
        exclude = ("friendly",)


class PersonTable(tables.Table):
    id = tables.Column().linkify()
    country = tables.Column().linkify()

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap.html"
