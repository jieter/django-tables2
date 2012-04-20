# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls.defaults import patterns, url
from django.shortcuts import render_to_response


def view(request):
    return render_to_response("template.html")


urlpatterns = patterns('',
    (r'^', view),
)
