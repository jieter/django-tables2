# coding: utf-8
from django.conf import settings
from django.conf.urls import patterns, include, url


from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('example.app.views',
    url(r'^$',             'multiple'),
    url(r'^class-based/$', 'class_based'),
    url(r'^tutorial/$',    'tutorial'),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
) + patterns('',
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
)
