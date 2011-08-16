# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url


from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', 'example.app.views.home', name='home'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
