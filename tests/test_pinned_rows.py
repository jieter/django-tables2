from django.test import SimpleTestCase

import django_tables2 as tables
from django_tables2.rows import BoundRow, BoundRows

from .utils import build_request, parse


class PinnedObj:
    def __init__(self, name, age):
        self.name = name
        self.age = age


class SimpleTable(tables.Table):
    name = tables.Column()
    occupation = tables.Column()
    age = tables.Column()

    def get_top_pinned_data(self):
        return [PinnedObj("Ron", 90), PinnedObj("Jon", 10)]

    def get_bottom_pinned_data(self):
        return [{"occupation": "Sum age", "age": 130}]


class PinnedRowsTest(SimpleTestCase):
    def test_bound_rows_with_pinned_data(self):
        record = {"name": "Grzegorz", "age": 30, "occupation": "programmer"}
        table = SimpleTable([record])

        self.assertEqual(len(table.rows), 4)  # rows + pinned data

        row = table.rows[0]

        with self.assertRaises(IndexError):
            table.rows[1]

        with self.assertRaises(IndexError):
            row.get_cell(3)

        self.assertEqual(row.get_cell("name"), record["name"])
        self.assertEqual(row.get_cell("occupation"), record["occupation"])
        self.assertEqual(row.get_cell("age"), record["age"])

        with self.assertRaises(KeyError):
            row.get_cell("gamma")

        self.assertIn("name", row)
        self.assertIn("occupation", row)
        self.assertNotIn("gamma", row)

    def test_as_html(self):
        """
        Ensure that html render correctly.
        """
        request = build_request("/")
        table = SimpleTable([{"name": "Grzegorz", "age": 30, "occupation": "programmer"}])
        root = parse(table.as_html(request))

        # One row for header
        self.assertEqual(len(root.findall(".//thead/tr")), 1)

        # In the header should be 3 cell.
        self.assertEqual(len(root.findall(".//thead/tr/th")), 3)

        # In the body, should be one original record and 3 pinned rows.
        self.assertEqual(len(root.findall(".//tbody/tr")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 12)

        # First top pinned row.
        tr = root.findall(".//tbody/tr")
        td = tr[0].findall("td")
        self.assertEqual(td[0].text, "Ron")
        self.assertEqual(td[1].text, table.default)
        self.assertEqual(td[2].text, "90")

        # Second top pinned row.
        td = tr[1].findall("td")
        self.assertEqual(td[0].text, "Jon")
        self.assertEqual(td[1].text, table.default)
        self.assertEqual(td[2].text, "10")

        # Original row
        td = tr[2].findall("td")
        self.assertEqual(td[0].text, "Grzegorz")
        self.assertEqual(td[1].text, "programmer")
        self.assertEqual(td[2].text, "30")

        # First bottom pinned row.
        td = tr[3].findall("td")
        self.assertEqual(td[0].text, table.default)
        self.assertEqual(td[1].text, "Sum age")
        self.assertEqual(td[2].text, "130")

    def test_pinned_row_attrs(self):
        """
        Testing attrs for pinned rows.
        """
        pinned_row_attrs = {"class": "super-mega-row", "data-foo": "bar"}

        request = build_request("/")
        record = {"name": "Grzegorz", "age": 30, "occupation": "programmer"}
        table = SimpleTable([record], pinned_row_attrs=pinned_row_attrs)
        html = table.as_html(request)

        self.assertIn("pinned-row", html)
        self.assertIn("super-mega-row", html)
        self.assertIn("data-foo", html)

    def test_ordering(self):
        """
        Change sorting should not change ordering pinned rows.
        """
        request = build_request("/")
        records = [
            {"name": "Alex", "age": 42, "occupation": "programmer"},
            {"name": "Greg", "age": 30, "occupation": "programmer"},
        ]

        table = SimpleTable(records, order_by="age")
        root = parse(table.as_html(request))
        tr = root.findall(".//tbody/tr")
        self.assertEqual(tr[0].findall("td")[2].text, "90")
        self.assertEqual(tr[1].findall("td")[2].text, "10")
        self.assertEqual(tr[2].findall("td")[2].text, "30")
        self.assertEqual(tr[3].findall("td")[2].text, "42")
        self.assertEqual(tr[4].findall("td")[2].text, "130")

        table = SimpleTable(records, order_by="-age")
        root = parse(table.as_html(request))
        tr = root.findall(".//tbody/tr")
        self.assertEqual(tr[0].findall("td")[2].text, "90")
        self.assertEqual(tr[1].findall("td")[2].text, "10")
        self.assertEqual(tr[2].findall("td")[2].text, "42")
        self.assertEqual(tr[3].findall("td")[2].text, "30")
        self.assertEqual(tr[4].findall("td")[2].text, "130")

    def test_bound_rows_getitem(self):
        """
        Testing BoundRows.__getitem__() method.
        Checking the return class for simple value and for slice.
        Ensure that inside of BoundRows pinned rows are included in length.
        """
        records = [
            {"name": "Greg", "age": 30, "occupation": "policeman"},
            {"name": "Alex", "age": 42, "occupation": "programmer"},
            {"name": "John", "age": 72, "occupation": "official"},
        ]

        table = SimpleTable(records, order_by="age")
        self.assertIsInstance(table.rows[0], BoundRow)
        self.assertIsInstance(table.rows[0:2], BoundRows)
        self.assertEqual(table.rows[0:2][0].get_cell("name"), "Greg")
        self.assertEqual(len(table.rows[:]), 6)

    def test_uniterable_pinned_data(self):
        """
        Ensure that, when data for pinned rows are not iterable,
        the ValueError exception will be raised.
        """

        class FooTable(tables.Table):
            col = tables.Column()

            def get_top_pinned_data(self):
                return 1

        tab = FooTable([1, 2, 3])

        with self.assertRaises(ValueError):
            for row in tab.rows:
                pass
