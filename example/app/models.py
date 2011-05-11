from django.db import models


class Country(models.Model):
    """Represents a geographical Country"""
    name = models.CharField(max_length=100)
    population = models.PositiveIntegerField()
    tz = models.CharField(max_length=50)
    visits = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = 'Countries'

    def __unicode__(self):
        return self.name
