# coding: utf-8
from __future__ import unicode_literals

from random import randint, sample

from django.test import TestCase
from django.utils.html import format_html, mark_safe, strip_tags

import django_tables2 as tables
from tests.app.models import Person


class ManyToManyColumnTest(TestCase):
    FAKE_NAMES = (
        ("Kyle", "Strader"),
        ("Francis", "Fisher"),
        ("James", "Jury"),
        ("Florentina", "Floyd"),
        ("Mark", "Boyd"),
        ("Simone", "Fong"),
    )

    def setUp(self):
        for first, last in self.FAKE_NAMES:
            Person.objects.create(first_name=first, last_name=last)

        persons = list(Person.objects.all())

        # give everyone 1 to 3 friends
        for person in persons:
            person.friends.add(*sample(persons, randint(1, 3)))
            person.save()

    def test_ManyToManyColumn_from_model(self):
        """
        Automatically uses the ManyToManyColumn for a ManyToManyField, and calls the
        Models's `__str__` method to transform the model instace to string.
        """

        class Table(tables.Table):
            name = tables.Column(accessor="name", order_by=("last_name", "first_name"))

            class Meta:
                model = Person
                fields = ("name", "friends")

        table = Table(Person.objects.all())

        for row in table.rows:
            friends = row.get_cell("friends").split(", ")

            for friend in friends:
                assert Person.objects.filter(first_name=friend).exists()

    def test_custom_separator(self):
        def assert_sep(sep):
            class Table(tables.Table):
                friends = tables.ManyToManyColumn(separator=sep)

            table = Table(Person.objects.all().order_by("last_name"))
            for row in table.rows:
                friends = row.get_cell("friends").split(sep)

                for friend in friends:
                    assert Person.objects.filter(first_name=friend).exists()

        # normal string, will not be escaped
        assert_sep("|")

        # html tag, would normally be escaped, but should not be escaped because
        # it is mark_safe()'ed
        assert_sep(mark_safe("<br />"))

    def test_transform_returns_html(self):
        class Table(tables.Table):
            friends = tables.ManyToManyColumn(
                transform=lambda m: format_html("<span>{}</span>", m.first_name)
            )

        table = Table(Person.objects.all().order_by("last_name"))
        for row in table.rows:
            friends = row.get_cell("friends").split(", ")
            for friend in friends:
                stripped = strip_tags(friend)
                assert Person.objects.filter(first_name=stripped).exists()

    def test_orderable_is_false(self):
        class Table(tables.Table):
            friends = tables.ManyToManyColumn(orderable=False)

        Table([])
        # TODO: assertions

    def test_ManyToManyColumn_complete_example(self):
        # add a friendless person
        remi = Person.objects.create(first_name="Remi", last_name="Barberin")

        class Table(tables.Table):
            name = tables.Column(accessor="name", order_by=("last_name", "first_name"))
            friends = tables.ManyToManyColumn(
                transform=lambda o: o.name, filter=lambda o: o.order_by("-last_name")
            )

        table = Table(Person.objects.all().order_by("last_name"))
        for row in table.rows:
            friends = row.get_cell("friends")
            if friends == "-":
                assert row.get_cell("name") == remi.name
                continue

            friends = list(map(lambda o: o.split(" "), friends.split(", ")))

            assert friends == sorted(friends, key=lambda item: item[1], reverse=True)
