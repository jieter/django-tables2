# coding: utf-8
from random import choice

from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.lorem_ipsum import words
from django.views.generic.base import TemplateView
from django_filters.views import FilterView

from django_tables2 import MultiTableMixin, RequestConfig, SingleTableMixin, SingleTableView

from .data import COUNTRIES
from .filters import PersonFilter
from .models import Country, Person
from .tables import Bootstrap4Table, BootstrapTable, CountryTable, PersonTable, SemanticTable, ThemedCountryTable


def create_fake_data():
    # create some fake data to make sure we need to paginate
    if Country.objects.all().count() < 50:
        for country in COUNTRIES.splitlines():
            name, population = country.split(';')
            Country.objects.create(name=name, visits=0, population=int(population))

    if Person.objects.all().count() < 500:
        countries = list(Country.objects.all()) + [None]
        Person.objects.bulk_create([
            Person(name=words(3, common=False), country=choice(countries))
            for i in range(50)
        ])


def index(request):
    create_fake_data()
    table = PersonTable(Person.objects.all())
    RequestConfig(request, paginate={
        'per_page': 5
    }).configure(table)

    return render(request, 'index.html', {
        'table': table,
        'urls': (
            (reverse('tutorial'), 'Tutorial'),
            (reverse('multiple'), 'Multiple tables'),
            (reverse('filtertableview'), 'Filtered tables'),
            (reverse('singletableview'), 'Using SingleTableMixin'),
            (reverse('multitableview'), 'Using MultiTableMixin'),
            (reverse('bootstrap'), 'template: Bootstrap 3 (bootstrap.html)'),
            (reverse('bootstrap4'), 'template: Bootstrap 4 (bootstrap4.html)'),
            (reverse('semantic'), 'template: Semantic UI (semantic.html)'),
        )
    })


def multiple(request):
    qs = Country.objects.all()

    example1 = CountryTable(qs, prefix='1-')
    RequestConfig(request, paginate=False).configure(example1)

    example2 = CountryTable(qs, prefix='2-')
    RequestConfig(request, paginate={'per_page': 2}).configure(example2)

    example3 = ThemedCountryTable(qs, prefix='3-')
    RequestConfig(request, paginate={'per_page': 3}).configure(example3)

    example4 = ThemedCountryTable(qs, prefix='4-')
    RequestConfig(request, paginate={'per_page': 3}).configure(example4)

    example5 = ThemedCountryTable(qs, prefix='5-')
    example5.template = 'extended_table.html'
    RequestConfig(request, paginate={'per_page': 3}).configure(example5)

    return render(request, 'multiple.html', {
        'example1': example1,
        'example2': example2,
        'example3': example3,
        'example4': example4,
        'example5': example5,
    })


def bootstrap(request):
    '''Demonstrate the use of the bootstrap template'''

    create_fake_data()
    table = BootstrapTable(Person.objects.all(), order_by='-name')
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    return render(request, 'bootstrap_template.html', {
        'table': table
    })


def bootstrap4(request):
    '''Demonstrate the use of the bootstrap4 template'''

    create_fake_data()
    table = Bootstrap4Table(Person.objects.all(), order_by='-name')
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    return render(request, 'bootstrap4_template.html', {
        'table': table
    })


def semantic(request):
    '''Demonstrate the use of the Semantic UI template'''

    create_fake_data()
    table = SemanticTable(Person.objects.all(), order_by='-name')
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    return render(request, 'semantic_template.html', {
        'table': table
    })


class ClassBased(SingleTableView):
    table_class = ThemedCountryTable
    queryset = Country.objects.all()
    template_name = 'class_based.html'


# note that this is not really the way to go because the queryset is not re
# -evaluated after the first time the view is requested.
qs = Person.objects.all()


class MultipleTables(MultiTableMixin, TemplateView):
    template_name = 'multiTable.html'
    tables = [
        PersonTable(qs),
        PersonTable(qs, exclude=('country', ))
    ]

    table_pagination = {
        'per_page': 10
    }


def tutorial(request):
    return render(request, 'tutorial.html', {'people': Person.objects.all()})


class FilteredPersonListView(SingleTableMixin, FilterView):
    table_class = PersonTable
    model = Person
    template_name = 'bootstrap_template.html'

    filterset_class = PersonFilter


def country_detail(request, pk):
    country = get_object_or_404(Country, pk=pk)
    return render(request, 'country_detail.html', {
        'country': country
    })
