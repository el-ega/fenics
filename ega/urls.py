from django.conf.urls import patterns, url

urlpatterns = patterns('ega.views',
    url(r'^$', 'home', name='home'),
    url(r'^(?P<slug>[\w-]+)/matches/$', 'next_matches',
        name='ega-next-matches'),
)
