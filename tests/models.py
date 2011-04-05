from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner
from django.test.client import RequestFactory
from django.template import Template, Context
from django.core.paginator import *
import django_tables as tables
import itertools
from django_attest import TestContext
from attest import Tests, Assert
from .testapp.models import Person, Occupation


models = Tests()
models.context(TestContext())

runner = DjangoTestSuiteRunner()
runner.setup_databases()


@models.context
def samples():
    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()
        occupation = tables.Column()

    # Test data
    occupation = Occupation.objects.create(name='Programmer')
    Person.objects.create(first_name='Bradley', last_name='Ayers', occupation=occupation)
    Person.objects.create(first_name='Chris',   last_name='Doble', occupation=occupation)

    yield PersonTable


@models.test
def boundrows_iteration(client, PersonTable):
    table = PersonTable(Person.objects.all())
    records = [row.record for row in table.rows]
    expecteds = Person.objects.all()
    for expected, actual in itertools.izip(expecteds, records):
        Assert(expected) == actual
