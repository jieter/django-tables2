from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views import static

from app.views import (
    ClassBased,
    FilteredPersonListView,
    MultipleTables,
    bootstrap,
    bootstrap4,
    bulma,
    checkbox,
    country_detail,
    index,
    multiple,
    person_detail,
    semantic,
    tutorial,
)

urlpatterns = [
    path("", index),
    path("multiple/", multiple, name="multiple"),
    path("class-based/", ClassBased.as_view(), name="singletableview"),
    path("class-based-multiple/", MultipleTables.as_view(), name="multitableview"),
    path("class-based-filtered/", FilteredPersonListView.as_view(), name="filtertableview"),
    path("checkbox/", checkbox, name="checkbox"),
    path("tutorial/", tutorial, name="tutorial"),
    path("bootstrap/", bootstrap, name="bootstrap"),
    path("bootstrap4/", bootstrap4, name="bootstrap4"),
    path("semantic/", semantic, name="semantic"),
    path("bulma/", bulma, name="bulma"),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("country/<int:pk>/", country_detail, name="country_detail"),
    path("person/<int:pk>/", person_detail, name="person_detail"),
    path("media/<path>", static.serve, {"document_root": settings.MEDIA_ROOT}),
    path("i18n/", include("django.conf.urls.i18n")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
