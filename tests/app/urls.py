# coding: utf-8
try:
    from django.conf.urls import url
except ImportError:
    from django.conf.urls.defaults import url
from . import views

urlpatterns = [
    url(r'^people/(?P<pk>\d+)/$', views.person, name='person'),
    url(r'^occupations/(?P<pk>\d+)/$', views.occupation, name='occupation'),
    url(r'^&\'"/(?P<pk>\d+)/$', lambda req: None, name='escaping'),
]
