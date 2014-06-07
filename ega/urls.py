from django.conf.urls import patterns, url


urlpatterns = patterns(
    'ega.views',
    url(r'^$', 'home', name='home'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^profile/verify/(?P<email>.+)/$', 'verify_email',
        name='verify-email'),
    url(r'^league/$', 'leagues', name='leagues'),
    url(r'^invite/$', 'invite_friends', name='invite'),
    url(r'^invite/(?P<league_slug>[\w-]+)/$', 'invite_friends',
        name='invite-league'),
    url(r'^join/(?P<key>\w+)/$', 'friend_join', name='join'),
    url(r'^join/(?P<key>\w+)/(?P<league_slug>[\w-]+)/$', 'friend_join',
        name='join'),
    url(r'^(?P<slug>[\w-]+)/matches/$', 'next_matches',
        name='ega-next-matches'),
    url(r'^(?P<slug>[\w-]+)/ranking/$', 'ranking', name='ega-ranking'),
    url(r'^(?P<slug>[\w-]+)/history/$', 'history', name='ega-history'),
)
