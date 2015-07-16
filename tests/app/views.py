<<<<<<< HEAD
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
=======
from django.shortcuts import redirect, render_to_response


def view(request):
    return render_to_response("template.html")


def bouncer(request):
    return redirect("https://example.com:1234/foo/?a=b#bar")
>>>>>>> upstream/master
