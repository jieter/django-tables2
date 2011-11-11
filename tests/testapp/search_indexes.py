from haystack.indexes import CharField, SearchIndex
from haystack import site
from .models import Person


class PersonIndex(SearchIndex):
    first_name = CharField(document=True)


site.register(Person, PersonIndex)
