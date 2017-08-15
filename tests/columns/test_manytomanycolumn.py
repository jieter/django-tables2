# coding: utf-8
from __future__ import unicode_literals

from random import randint, sample

import pytest

import django_tables2 as tables
from tests.app.models import Person

FAKE_NAMES = (
    ('Kyle', 'Strader'),
    ('Francis', 'Fisher'),
    ('James', 'Jury'),
    ('Florentina', 'Floyd'),
    ('Mark', 'Boyd'),
    ('Simone', 'Fong'),
)


def create_Persons():
    for first, last in FAKE_NAMES:
        Person.objects.create(first_name=first, last_name=last)

    persons = list(Person.objects.all())

    # give everyone 1 to 3 friends
    for person in persons:
        person.friends.add(*sample(persons, randint(1, 3)))
        person.save()


@pytest.mark.django_db
def test_ManyToManyColumn_from_model():
    '''
    Automaticcally uses the ManyToManyColumn for a ManyToManyField, and calls the
    Models's `__str__` method to transform the model instace to string.
    '''
    create_Persons()

    class Table(tables.Table):
        name = tables.Column(accessor='name', order_by=('last_name', 'first_name'))

        class Meta:
            model = Person
            fields = ('name', 'friends')

    table = Table(Person.objects.all())

    for row in table.rows:
        friends = row.get_cell('friends').split(', ')

        for friend in friends:
            assert Person.objects.filter(first_name=friend).exists()


@pytest.mark.django_db
def test_ManyToManyColumn_complete_exmplae():
    create_Persons()

    # add a friendless person
    remi = Person.objects.create(first_name='Remi', last_name='Barberin')

    class Table(tables.Table):
        name = tables.Column(accessor='name', order_by=('last_name', 'first_name'))
        friends = tables.ManyToManyColumn(
            transform=lambda o: o.name,
            filter=lambda o: o.order_by('-last_name')
        )

    table = Table(Person.objects.all().order_by('last_name'))
    for row in table.rows:
        friends = row.get_cell('friends')
        if friends == '-':
            assert row.get_cell('name') == remi.name
            continue

        friends = list(map(lambda o: o.split(' '), friends.split(', ')))

        assert friends == sorted(friends, key=lambda item: item[1], reverse=True)
