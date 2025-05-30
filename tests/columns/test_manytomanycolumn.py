from random import randint, sample

from django.test import TestCase
from django.utils.html import format_html, mark_safe, strip_tags

import django_tables2 as tables
from tests.app.models import Group, Occupation, Person


class ManyToManyColumnTest(TestCase):
    FAKE_NAMES = (
        ("Kyle", "Strader"),
        ("Francis", "Fisher"),
        ("James", "Jury"),
        ("Florentina", "Floyd"),
        ("Mark", "Boyd"),
        ("Simone", "Fong"),
    )

    @classmethod
    def setUpTestData(cls):
        cls.carpenter = Occupation.objects.create(name="Carpenter")
        for first, last in cls.FAKE_NAMES:
            Person.objects.create(first_name=first, last_name=last, occupation=cls.carpenter)

        persons = list(Person.objects.all())
        # give everyone 1 to 3 friends
        for person in persons:
            person.friends.add(*sample(persons, randint(1, 3)))

        # Add a person without friends
        cls.remi = Person.objects.create(first_name="Remi", last_name="Barberin")

        cls.developers = Group.objects.create(name="developers")
        cls.developers.members.add(
            Person.objects.get(first_name="James"), Person.objects.get(first_name="Simone")
        )

    def test_from_model(self):
        """
        Test if ManyToManyColumn is used for ManyToManyFields.


        Should automatically use  ManyToManyColumn for a ManyToManyField, and calls the
        Models's `__str__` method to transform the model instance to string.
        """

        class Table(tables.Table):
            name = tables.Column(accessor="name", order_by=("last_name", "first_name"))

            class Meta:
                model = Person
                fields = ("name", "friends")

        table = Table(Person.objects.all())

        for row in table.rows:
            cell = row.get_cell("friends")
            if cell is table.default:
                continue

            for friend in cell.split(", "):
                self.assertTrue(Person.objects.filter(first_name=friend).exists())

    def test_linkify_item(self):
        class Table(tables.Table):
            name = tables.Column(accessor="name", order_by=("last_name", "first_name"))
            friends = tables.ManyToManyColumn(linkify_item=True)

        table = Table(Person.objects.all())
        for row in table.rows:
            friends = row.get_cell("friends")

            for friend in row.record.friends.all():
                self.assertIn(friend.get_absolute_url(), friends)
                self.assertIn(str(friend), friends)

    def test_linkify_item_different_model(self):
        """Make sure the correct get_absolute_url() is used to linkify the items."""

        class GroupTable(tables.Table):
            name = tables.Column(linkify=True)
            members = tables.ManyToManyColumn(linkify_item=True)

        row = GroupTable(Group.objects.all()).rows[0]
        self.assertEqual(
            row.get_cell("name"),
            f'<a href="/group/{self.developers.pk}/">{self.developers.name}</a>',
        )
        self.assertEqual(
            row.get_cell("members"),
            '<a href="/people/3/">James</a>, <a href="/people/6/">Simone</a>',
        )

    def test_linkify_item_foreign_key(self):
        class OccupationTable(tables.Table):
            name = tables.Column(linkify=True)
            people = tables.ManyToManyColumn(linkify_item=True)

        row = OccupationTable(Occupation.objects.all()).rows[0]
        self.assertEqual(
            row.get_cell("name"),
            f'<a href="/occupations/{self.carpenter.pk}/">{self.carpenter.name}</a>',
        )
        self.assertEqual(
            row.get_cell("people"),
            ", ".join(
                (
                    '<a href="/people/1/">Kyle</a>',
                    '<a href="/people/2/">Francis</a>',
                    '<a href="/people/3/">James</a>',
                    '<a href="/people/4/">Florentina</a>',
                    '<a href="/people/5/">Mark</a>',
                    '<a href="/people/6/">Simone</a>',
                )
            ),
        )

    def test_custom_separator(self):
        def assert_sep(sep):
            class Table(tables.Table):
                friends = tables.ManyToManyColumn(separator=sep)

            table = Table(Person.objects.all().order_by("last_name"))

            for row in table.rows:
                cell = row.get_cell("friends")
                if cell is table.default:
                    continue

                for friend in cell.split(sep):
                    self.assertTrue(Person.objects.filter(first_name=friend).exists())

        # normal string, will not be escaped
        assert_sep("|")

        # html tag, would normally be escaped, but should not be escaped because it is mark_safe()'ed
        assert_sep(mark_safe("<br />"))

    def test_transform_returns_html(self):
        class Table(tables.Table):
            friends = tables.ManyToManyColumn(
                transform=lambda m: format_html("<span>{}</span>", m.first_name)
            )

        table = Table(Person.objects.all().order_by("last_name"))
        for row in table.rows:
            cell = row.get_cell("friends")
            if cell is table.default:
                continue

            for friend in cell.split(", "):
                stripped = strip_tags(friend)
                self.assertTrue(Person.objects.filter(first_name=stripped).exists())

    def test_orderable_is_false(self):
        class Table(tables.Table):
            friends = tables.ManyToManyColumn(orderable=False)

        table = Table([])

        self.assertFalse(table.columns["friends"].orderable)

    def test_complete_example(self):
        class Table(tables.Table):
            name = tables.Column(accessor="name", order_by=("last_name", "first_name"))
            friends = tables.ManyToManyColumn(
                transform=lambda o: o.name, filter=lambda o: o.order_by("-last_name")
            )

        table = Table(Person.objects.all().order_by("last_name"))
        for row in table.rows:
            friends = row.get_cell("friends")
            if friends is table.default:
                self.assertEqual(row.get_cell("name"), self.remi.name)
                continue

            # Verify the list is sorted descending
            friends = list(map(lambda o: o.split(" "), friends.split(", ")))
            self.assertEqual(friends, sorted(friends, key=lambda item: item[1], reverse=True))

    def test_default(self):
        """A ManyToManyColumn without explicit default should use the table default."""

        class Table(tables.Table):
            name = tables.Column(accessor="name", order_by=("last_name", "first_name"))
            friends = tables.ManyToManyColumn()

        table = Table(Person.objects.filter(first_name="Remi"))
        self.assertEqual(table.rows[0].get_cell("friends"), "—")

    def test_custom_default(self):
        """A ManyToManyColumn with explicit default should use it."""

        class Table(tables.Table):
            name = tables.Column(accessor="name", order_by=("last_name", "first_name"))
            friends = tables.ManyToManyColumn(default="--")

        table = Table(Person.objects.filter(first_name="Remi"))
        self.assertEqual(table.rows[0].get_cell("friends"), "--")
