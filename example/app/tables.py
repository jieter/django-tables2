import django_tables2 as tables

from .models import Country, Person


class CountryTable(tables.Table):
    name = tables.Column()
    population = tables.Column()
    tz = tables.Column(verbose_name="time zone")
    visits = tables.Column()
    summary = tables.Column(order_by=("name", "population"))

    class Meta:
        model = Country


class ThemedCountryTable(CountryTable):
    class Meta:
        attrs = {"class": "paleblue"}


class CheckboxTable(tables.Table):
    select = tables.CheckBoxColumn(empty_values=(), footer="")

    population = tables.Column(attrs={"cell": {"class": "population"}})

    class Meta:
        model = Country
        template_name = "django_tables2/bootstrap.html"
        fields = ("select", "name", "population")


class BootstrapTable(tables.Table):
    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap.html"
        fields = ("id", "country", "country__continent__name")
        linkify = ("country", "country__continent__name")


class BootstrapTablePinnedRows(BootstrapTable):
    class Meta(BootstrapTable.Meta):
        pinned_row_attrs = {"class": "info"}

    def get_top_pinned_data(self):
        return [
            {
                "name": "Most used country: ",
                "country": Country.objects.filter(name="Cameroon").first(),
            }
        ]


class Bootstrap4Table(tables.Table):
    country = tables.Column(linkify=True)
    continent = tables.Column(accessor="country__continent", linkify=True)

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-hover"}
        exclude = ("friendly",)


class Bootstrap5Table(tables.Table):
    country = tables.Column(linkify=True)
    continent = tables.Column(accessor="country__continent", linkify=True)

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap5.html"
        exclude = ("friendly",)


class SemanticTable(tables.Table):
    country = tables.Column(linkify=True)

    class Meta:
        model = Person
        template_name = "django_tables2/semantic.html"
        exclude = ("friendly",)


class PersonTable(tables.Table):
    id = tables.Column(linkify=True)
    country = tables.Column(linkify=True)

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap.html"
