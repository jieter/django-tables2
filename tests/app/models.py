# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext


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

    def __unicode__(self):
        return self.first_name


class Occupation(models.Model):
    name = models.CharField(max_length=200)
    region = models.ForeignKey('Region', null=True)

    def __unicode__(self):
        return self.name


class Region(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name


# -- haystack -----------------------------------------------------------------


from haystack import site
from haystack.indexes import CharField, SearchIndex

class PersonIndex(SearchIndex):
    first_name = CharField(document=True)

site.register(Person, PersonIndex)
