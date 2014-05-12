from django.conf.urls import patterns, url


urlpatterns = patterns(
    'ega.views',
    url(r'^$', 'home', name='home'),
    url(r'^invite/$', 'invite_friends', name='invite'),
    url(r'^invite/(?P<key>\w+)/$', 'friend_join', name='join'),
    url(r'^invite/(?P<key>\w+)/(?P<slug>[\w-]+)/$', 'friend_join', name='join'),
    url(r'^(?P<slug>[\w-]+)/matches/$', 'next_matches',
        name='ega-next-matches'),
    url(r'^(?P<slug>[\w-]+)/ranking/$', 'ranking', name='ega-ranking'),
)
