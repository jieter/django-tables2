from django.urls import path, re_path

from . import views

urlpatterns = [
    path("people/delete/<int:pk>/", views.person, name="person_delete"),
    path("people/edit/<int:pk>/", views.person, name="person_edit"),
    path("people/<int:pk>/", views.person, name="person"),
    path("occupations/<int:pk>/", views.occupation, name="occupation"),
    re_path(r'^&\'"/(?P<pk>\d+)/$', lambda req: None, name="escaping"),
]
