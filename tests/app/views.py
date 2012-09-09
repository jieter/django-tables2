# coding: utf-8
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Person, Occupation


def person(request, pk):
    """A really simple view to provide an endpoint for the 'person' URL."""
    person = get_object_or_404(Person, pk=pk)
    return HttpResponse('Person: %s' % person)


def occupation(request, pk):
    """
    Another really simple view to provide an endpoint for the 'occupation' URL.
    """
    occupation = get_object_or_404(Occupation, pk=pk)
    return HttpResponse('Occupation: %s' % occupation)
