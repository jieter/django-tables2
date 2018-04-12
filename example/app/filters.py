from django_filters import FilterSet

from .models import Person


class PersonFilter(FilterSet):
    class Meta:
        model = Person
        fields = {
            'name': ['exact', 'contains'],
            'country': ['exact']
        }
