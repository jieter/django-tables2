# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from .tables import CountryTable, ThemedCountryTable
from .models import Country
from django_tables2 import RequestConfig


def home(request):
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

    return render_to_response('example.html', {
        'example1': example1,
        'example2': example2,
        'example3': example3,
        'example4': example4,
        'example5': example5,
    }, context_instance=RequestContext(request))
