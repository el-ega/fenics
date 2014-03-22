from django.conf.urls import patterns, url

urlpatterns = patterns('ega.views',
    url(r'^(?P<slug>[\w-]+)/matches/$', 'next_matches',
        name='ega-next-matches'),
)
