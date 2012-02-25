# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from . import views


urlpatterns = patterns('',
    url(r'^people/(?P<pk>\d+)/$',      views.person,     name='person'),
    url(r'^occupations/(?P<pk>\d+)/$', views.occupation, name='occupation'),
    url(r'^&\'"/(?P<pk>\d+)/$',        lambda req: None, name='escaping'),
)
