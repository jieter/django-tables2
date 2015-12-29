# coding: utf-8
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views import static

from app.views import class_based, multiple, tutorial

admin.autodiscover()

urlpatterns = [
    url(r'^$', multiple),
    url(r'^class-based/$', class_based),
    url(r'^tutorial/$', tutorial),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^media/(?P<path>.*)$', static.serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
