from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .models import Occupation, Person


def person(request, pk):
    """View to serve as an endpoint for the 'person' URL."""
    person = get_object_or_404(Person, pk=pk)
    return HttpResponse(f"Person: {person}")


def occupation(request, pk):
    """Another really simple view to provide an endpoint for the 'occupation' URL."""
    occupation = get_object_or_404(Occupation, pk=pk)
    return HttpResponse(f"Occupation: {occupation}")
