from django.conf.urls import patterns, include, url


urlpatterns = patterns('ega.views',
    url(r'^$', 'home', name='home'),
)
