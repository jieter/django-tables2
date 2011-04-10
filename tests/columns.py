"""Test the core table functionality."""
from attest import Tests, Assert
import django_tables as tables
from django_tables import utils


columns = Tests()


@columns.test
def sortable():
    class SimpleTable(tables.Table):
        name = tables.Column()
    Assert(SimpleTable([]).columns['name'].sortable) is True

    class SimpleTable(tables.Table):
        name = tables.Column()
        
        class Meta:
            sortable = False
    Assert(SimpleTable([]).columns['name'].sortable) is False

    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            sortable = True
    Assert(SimpleTable([]).columns['name'].sortable) is True


