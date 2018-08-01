# coding: utf-8
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views import static

from app.views import (
    ClassBased,
    FilteredPersonListView,
    MultipleTables,
    bootstrap,
    bootstrap4,
    checkbox,
    country_detail,
    index,
    multiple,
    person_detail,
    semantic,
    tutorial,
)

urlpatterns = [
    url(r"^$", index),
    url(r"^multiple/", multiple, name="multiple"),
    url(r"^class-based/$", ClassBased.as_view(), name="singletableview"),
    url(r"^class-based-multiple/$", MultipleTables.as_view(), name="multitableview"),
    url(r"^class-based-filtered/$", FilteredPersonListView.as_view(), name="filtertableview"),
    url(r"^checkbox/$", checkbox, name="checkbox"),
    url(r"^tutorial/$", tutorial, name="tutorial"),
    url(r"^bootstrap/$", bootstrap, name="bootstrap"),
    url(r"^bootstrap4/$", bootstrap4, name="bootstrap4"),
    url(r"^semantic/$", semantic, name="semantic"),
    url(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    url(r"^admin/", admin.site.urls),
    url(r"^country/(?P<pk>[0-9]+)/$", country_detail, name="country_detail"),
    url(r"^person/(?P<pk>[0-9]+)/$", person_detail, name="person_detail"),
    url(r"^media/(?P<path>.*)$", static.serve, {"document_root": settings.MEDIA_ROOT}),
    url(r"^i18n/", include("django.conf.urls.i18n")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [url(r"^__debug__/", include(debug_toolbar.urls))] + urlpatterns
