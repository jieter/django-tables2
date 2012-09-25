# coding: utf-8
from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Country(models.Model):
    """Represents a geographical Country"""
    name = models.CharField(max_length=100)
    population = models.PositiveIntegerField(verbose_name="población")
    tz = models.CharField(max_length=50)
    visits = models.PositiveIntegerField()
    commonwealth = models.NullBooleanField()
    flag = models.FileField(upload_to="country/flags/")

    class Meta:
        verbose_name_plural = _("countries")

    def __unicode__(self):
        return self.name

    @property
    def summary(self):
        return "%s (pop. %s)" % (self.name, self.population)


class Person(models.Model):
    name = models.CharField(max_length=200, verbose_name="full name")

    class Meta:
        verbose_name_plural = "people"

    def __unicode__(self):
        return self.name
