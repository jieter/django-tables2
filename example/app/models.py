from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Continent(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Country(models.Model):
    """
    Represents a geographical Country
    """

    name = models.CharField(max_length=100)
    population = models.PositiveIntegerField(verbose_name=_("population"))
    tz = models.CharField(max_length=50, blank=True)
    visits = models.PositiveIntegerField()
    commonwealth = models.NullBooleanField()
    flag = models.FileField(upload_to="country/flags/", blank=True)

    continent = models.ForeignKey(Continent, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = _("countries")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("country_detail", args=(self.pk,))

    @property
    def summary(self):
        return "%s (pop. %s)" % (self.name, self.population)


class Person(models.Model):
    name = models.CharField(max_length=200, verbose_name="full name")
    friendly = models.BooleanField(default=True)

    country = models.ForeignKey(Country, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "people"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("person_detail", args=(self.pk,))
