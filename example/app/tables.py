import django_tables2 as tables
from django.utils.translation import ugettext_lazy as _

class CountryTable(tables.Table):
    name = tables.Column( verbose_name = _(u'different name'))
    population = tables.Column()
    tz = tables.Column(verbose_name='Time Zone')
    visits = tables.Column()


class ThemedCountryTable(CountryTable):
    class Meta:
        attrs = {'class': 'paleblue'}
