# coding: utf-8
from django.contrib import admin
from .models import Country


class CountryAdmin(admin.ModelAdmin):
    list_per_page = 2
admin.site.register(Country, CountryAdmin)
