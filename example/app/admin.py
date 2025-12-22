from django.contrib import admin

from .models import Continent, Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_per_page = 20

    list_display = ("name", "continent")


admin.site.register(Continent)
