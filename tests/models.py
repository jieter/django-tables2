import itertools
from django.conf import settings
from django.test.client import RequestFactory
from django.template import Template, Context
import django_tables as tables
from django_attest import TransactionTestContext
from attest import Tests, Assert
from .testapp.models import Person, Occupation


models = Tests()
models.context(TransactionTestContext())


class PersonTable(tables.Table):
    first_name = tables.Column()
    last_name = tables.Column()
    occupation = tables.Column()


@models.test
def boundrows_iteration():
    occupation = Occupation.objects.create(name='Programmer')
    Person.objects.create(first_name='Bradley', last_name='Ayers', occupation=occupation)
    Person.objects.create(first_name='Chris',   last_name='Doble', occupation=occupation)

    table = PersonTable(Person.objects.all())
    records = [row.record for row in table.rows]
    expecteds = Person.objects.all()
    for expected, actual in itertools.izip(expecteds, records):
        Assert(expected) == actual
