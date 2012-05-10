try:
    from django.conf.urls import patterns
except ImportError:
    from django.conf.urls.defaults import patterns


urlpatterns = patterns('tests.app.views',
    (r'^bouncer/', 'bouncer'),
    (r'^',         'view'),
)
