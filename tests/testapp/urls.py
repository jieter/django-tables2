from django.conf.urls.defaults import patterns, include, url
from . import views


urlpatterns = patterns('',
    url(r'^people/(?P<pk>\d+)/$',      views.person,     name='person'),
    url(r'^occupations/(?P<pk>\d+)/$', views.occupation, name='occupation'),
)
