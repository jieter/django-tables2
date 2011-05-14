from django.conf.urls.defaults import patterns, include, url
from . import views


urlpatterns = patterns('',
    url(r'^people/(\d+)/$',      views.person,     name='person'),
    url(r'^occupations/(\d+)/$', views.occupation, name='occupation'),
)
