from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^people/delete/(?P<pk>\d+)/$", views.person, name="person_delete"),
    url(r"^people/edit/(?P<pk>\d+)/$", views.person, name="person_edit"),
    url(r"^people/(?P<pk>\d+)/$", views.person, name="person"),
    url(r"^occupations/(?P<pk>\d+)/$", views.occupation, name="occupation"),
    url(r'^&\'"/(?P<pk>\d+)/$', lambda req: None, name="escaping"),
]
