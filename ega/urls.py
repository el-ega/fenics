from django.conf.urls import patterns, url

urlpatterns = patterns(
    'ega.views',
    url(r'^$', 'home', name='home'),
    url(r'^invite/twit/$', 'invite_friends_via_twitter', name='twit'),
    url(r'^(?P<slug>[\w-]+)/matches/$', 'next_matches',
        name='ega-next-matches'),
)
