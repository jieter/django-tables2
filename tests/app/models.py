# coding: utf-8
from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import six
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy


@six.python_2_unicode_compatible
class Person(models.Model):
    first_name = models.CharField(max_length=200)

    last_name = models.CharField(max_length=200, verbose_name="surname")

    occupation = models.ForeignKey(
        "Occupation",
        related_name="people",
        null=True,
        verbose_name="occupation of the person",
        on_delete=models.CASCADE,
    )

    trans_test = models.CharField(
        max_length=200, blank=True, verbose_name=ugettext("translation test")
    )

    trans_test_lazy = models.CharField(
        max_length=200, blank=True, verbose_name=ugettext_lazy("translation test lazy")
    )

    safe = models.CharField(max_length=200, blank=True, verbose_name=mark_safe("<b>Safe</b>"))

    website = models.URLField(max_length=200, null=True, blank=True, verbose_name="web site")

    birthdate = models.DateField(null=True)

    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    foreign_key = GenericForeignKey()

    friends = models.ManyToManyField("Person")

    class Meta:
        verbose_name = "person"
        verbose_name_plural = "people"

    def __str__(self):
        return self.first_name

    @property
    def name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def get_absolute_url(self):
        return reverse("person", args=(self.pk,))


class PersonProxy(Person):
    class Meta:
        proxy = True
        ordering = ("last_name",)


class Group(models.Model):
    name = models.CharField(max_length=200)
    members = models.ManyToManyField("Person")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/group/{}/".format(self.pk)


@six.python_2_unicode_compatible
class Occupation(models.Model):
    name = models.CharField(max_length=200)
    region = models.ForeignKey("Region", null=True, on_delete=models.CASCADE)
    boolean = models.NullBooleanField(null=True)
    boolean_with_choices = models.NullBooleanField(
        null=True, choices=((True, "Yes"), (False, "No"))
    )

    def get_absolute_url(self):
        return reverse("occupation", args=(self.pk,))

    def __str__(self):
        return self.name


@six.python_2_unicode_compatible
class Region(models.Model):
    name = models.CharField(max_length=200)
    mayor = models.OneToOneField(Person, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PersonInformation(models.Model):
    person = models.ForeignKey(
        Person, related_name="info_list", verbose_name="Information", on_delete=models.CASCADE
    )
