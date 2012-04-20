from __future__ import unicode_literals
from django.db import models


class Thing(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name
