from random import choice

from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.lorem_ipsum import words
from django.views.generic.base import TemplateView
from django_filters.views import FilterView

from django_tables2 import MultiTableMixin, RequestConfig, SingleTableMixin, SingleTableView
from django_tables2.export.views import ExportMixin
from django_tables2.paginators import LazyPaginator

from .data import COUNTRIES
from .filters import PersonFilter
from .models import Country, Person
from .tables import (
    Bootstrap4Table,
    BootstrapTable,
    BootstrapTablePinnedRows,
    CheckboxTable,
    CountryTable,
    PersonTable,
    SemanticTable,
    ThemedCountryTable,
)


def create_fake_data():
    # create some fake data to make sure we need to paginate
    if Country.objects.all().count() < 50:
        for country in COUNTRIES.splitlines():
            name, population = country.split(";")
            Country.objects.create(name=name, visits=0, population=int(population))

    if Person.objects.all().count() < 500:
        countries = list(Country.objects.all()) + [None]
        Person.objects.bulk_create(
            [Person(name=words(3, common=False), country=choice(countries)) for i in range(50)]
        )


def index(request):
    create_fake_data()
    table = PersonTable(Person.objects.all())
    RequestConfig(request, paginate={"per_page": 5}).configure(table)

    return render(
        request,
        "index.html",
        {
            "table": table,
            "urls": (
                (reverse("tutorial"), "Tutorial"),
                (reverse("multiple"), "Multiple tables"),
                (reverse("filtertableview"), "Filtered tables (with export)"),
                (reverse("singletableview"), "Using SingleTableMixin"),
                (reverse("multitableview"), "Using MultiTableMixin"),
                (reverse("bootstrap"), "template: Bootstrap 3 (bootstrap.html)"),
                (reverse("bootstrap4"), "template: Bootstrap 4 (bootstrap4.html)"),
                (reverse("semantic"), "template: Semantic UI (semantic.html)"),
            ),
        },
    )


def multiple(request):
    qs = Country.objects.all()

    example1 = CountryTable(qs, prefix="1-")
    RequestConfig(request, paginate=False).configure(example1)

    example2 = CountryTable(qs, prefix="2-")
    RequestConfig(request, paginate={"per_page": 2}).configure(example2)

    example3 = ThemedCountryTable(qs, prefix="3-")
    RequestConfig(request, paginate={"per_page": 3}).configure(example3)

    example4 = ThemedCountryTable(qs, prefix="4-")
    RequestConfig(request, paginate={"per_page": 3}).configure(example4)

    example5 = ThemedCountryTable(qs, prefix="5-")
    example5.template = "extended_table.html"
    RequestConfig(request, paginate={"per_page": 3}).configure(example5)

    return render(
        request,
        "multiple.html",
        {
            "example1": example1,
            "example2": example2,
            "example3": example3,
            "example4": example4,
            "example5": example5,
        },
    )


def checkbox(request):
    create_fake_data()
    table = CheckboxTable(Country.objects.all(), order_by="name")
    RequestConfig(request, paginate={"per_page": 15}).configure(table)

    return render(request, "checkbox_example.html", {"table": table})


def bootstrap(request):
    """Demonstrate the use of the bootstrap template"""

    create_fake_data()
    table = BootstrapTable(Person.objects.all().select_related("country"), order_by="-name")
    RequestConfig(request, paginate={"paginator_class": LazyPaginator, "per_page": 10}).configure(
        table
    )

    return render(request, "bootstrap_template.html", {"table": table})


def bootstrap4(request):
    """Demonstrate the use of the bootstrap4 template"""

    create_fake_data()
    table = Bootstrap4Table(Person.objects.all(), order_by="-name")
    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    return render(request, "bootstrap4_template.html", {"table": table})


def semantic(request):
    """Demonstrate the use of the Semantic UI template"""

    create_fake_data()
    table = SemanticTable(Person.objects.all(), order_by="-name")
    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    return render(request, "semantic_template.html", {"table": table})


class ClassBased(SingleTableView):
    table_class = ThemedCountryTable
    queryset = Country.objects.all()
    template_name = "class_based.html"


class MultipleTables(MultiTableMixin, TemplateView):
    template_name = "multiTable.html"

    table_pagination = {"per_page": 10}

    def get_tables(self):
        qs = Person.objects.all()
        return [
            PersonTable(qs),
            PersonTable(qs, exclude=("country",)),
            BootstrapTablePinnedRows(qs),
        ]


def tutorial(request):
    table = PersonTable(
        Person.objects.all(), attrs={"class": "paleblue"}, template_name="django_tables2/table.html"
    )
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    return render(request, "tutorial.html", {"table": table})


class FilteredPersonListView(ExportMixin, SingleTableMixin, FilterView):
    table_class = PersonTable
    model = Person
    template_name = "bootstrap_template.html"

    filterset_class = PersonFilter

    export_formats = ("csv", "xls")

    def get_queryset(self):
        return super().get_queryset().select_related("country")

    def get_table_kwargs(self):
        return {"template_name": "django_tables2/bootstrap.html"}


def country_detail(request, pk):
    country = get_object_or_404(Country, pk=pk)

    # hide the country column, as it is not very interesting for a list of persons for a country.
    table = PersonTable(country.person_set.all(), extra_columns=(("country", None),))
    return render(request, "country_detail.html", {"country": country, "table": table})


def person_detail(request, pk):
    person = get_object_or_404(Person, pk=pk)

    return render(request, "person_detail.html", {"person": person})
