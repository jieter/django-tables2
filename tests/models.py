from django.conf import settings
from django.core.paginator import *
import django_tables as tables
from django_attest import TestContext
from attest import Tests
from .testapp.models import Person


models = Tests()
models.context(TestContext())


@models.context
def samples():
    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()

    # we're going to test against User, so let's create a few
    Person.objects.create(first_name='Bradley', last_name='Ayers')
    Person.objects.create(first_name='Chris',   last_name='Doble')

    yield PersonTable


@models.test
def simple(client, UserTable):
    queryset = Person.objects.all()
    table = PersonTable(queryset)

    for index, row in enumerate(table.rows):
        person = queryset[index]
        Assert(person.username) == row['first_name']
        Assert(person.email) == row['last_name']
