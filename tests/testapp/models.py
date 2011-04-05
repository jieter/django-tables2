from django.db import models


class Person(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    occupation = models.ForeignKey('Occupation', related_name='people')

    def __unicode__(self):
        return self.first_name


class Occupation(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
