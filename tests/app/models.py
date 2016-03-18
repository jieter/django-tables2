# coding: utf-8
from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import six
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy


@six.python_2_unicode_compatible
class Person(models.Model):
    first_name = models.CharField(max_length=200)

    last_name = models.CharField(max_length=200, verbose_name='surname')

    occupation = models.ForeignKey(
        'Occupation', related_name='people',
        null=True, verbose_name='occupation')

    trans_test = models.CharField(
        max_length=200, blank=True,
        verbose_name=ugettext("translation test"))

    trans_test_lazy = models.CharField(
        max_length=200, blank=True,
        verbose_name=ugettext_lazy("translation test lazy"))

    safe = models.CharField(
        max_length=200, blank=True, verbose_name=mark_safe("<b>Safe</b>"))

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    foreign_key = GenericForeignKey()

    class Meta:
        verbose_name = "person"
        verbose_name_plural = "people"

    def __str__(self):
        return self.first_name

    @property
    def name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def get_absolute_url(self):
        return reverse('person', args=(self.pk, ))


class PersonProxy(Person):
    class Meta:
        proxy = True
        ordering = ('last_name', )


@six.python_2_unicode_compatible
class Occupation(models.Model):
    name = models.CharField(max_length=200)
    region = models.ForeignKey('Region', null=True)
    boolean = models.BooleanField(default=True, choices=(
        (True, 'Yes'),
        (False, 'No')
    ))

    def get_absolute_url(self):
        return reverse('occupation', args=(self.pk, ))

    def __str__(self):
        return self.name


@six.python_2_unicode_compatible
class Region(models.Model):
    name = models.CharField(max_length=200)
    mayor = models.OneToOneField(Person, null=True)

    def __str__(self):
        return self.name


class PersonInformation(models.Model):
    person = models.ForeignKey(
        Person, related_name='info_list', verbose_name='Information')


# -- haystack -----------------------------------------------------------------

if not six.PY3:  # Haystack isn't compatible with Python 3
    from haystack import indexes

    class PersonIndex(indexes.SearchIndex, indexes.Indexable):
        first_name = indexes.CharField(document=True)

        def get_model(self):
            return Person

        def index_queryset(self, using=None):
            return self.get_model().objects.all()
