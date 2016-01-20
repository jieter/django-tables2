# coding: utf-8
from random import choice

from django.shortcuts import render

from django_tables2 import RequestConfig, SingleTableView

from .models import Country, Person
from .tables import BootstrapTable, CountryTable, ThemedCountryTable

try:
    from django.utils.lorem_ipsum import words
except ImportError:
    # django 1.7 has lorem_ipsum in contrib.webdisign, moved in 1.8
    from django.contrib.webdesign.lorem_ipsum import words


def multiple(request):
    qs = Country.objects.all()

    example1 = CountryTable(qs, prefix="1-")
    RequestConfig(request, paginate=False).configure(example1)

    example2 = CountryTable(qs, prefix="2-")
    RequestConfig(request, paginate={"per_page": 2}).configure(example2)

    example3 = ThemedCountryTable(qs, prefix="3-")
    RequestConfig(request, paginate={"per_page": 3}).configure(example3)

    example4 = ThemedCountryTable(qs, prefix="4-")
    RequestConfig(request, paginate={"per_page": 3}).configure(example4)

    example5 = ThemedCountryTable(qs, prefix="5-")
    example5.template = "extended_table.html"
    RequestConfig(request, paginate={"per_page": 3}).configure(example5)

    return render(request, 'multiple.html', {
        'example1': example1,
        'example2': example2,
        'example3': example3,
        'example4': example4,
        'example5': example5,
    })


def bootstrap(request):
    '''Demonstrate the use of the bootstrap template'''
    # create some fake data to make sure we need to paginate
    if Person.objects.all().count() < 50:
        countries = list(Country.objects.all()) + [None]
        Person.objects.bulk_create([
            Person(name=words(3, common=False), country=choice(countries))
            for i in range(50)
        ])

    table = BootstrapTable(Person.objects.all())
    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    return render(request, 'bootstrap_template.html', {
        'table': table
    })


class ClassBased(SingleTableView):
    table_class = ThemedCountryTable
    queryset = Country.objects.all()
    template_name = "class_based.html"

class_based = ClassBased.as_view()


def tutorial(request):
    return render(request, "tutorial.html", {"people": Person.objects.all()})
