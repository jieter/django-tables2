# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Country(models.Model):
    """Represents a geographical Country"""
    name = models.CharField(max_length=100)
    population = models.PositiveIntegerField(verbose_name=u"Población")
    tz = models.CharField(max_length=50)
    visits = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = _("Countries")

    def __unicode__(self):
        return self.name
