from django.conf.urls import patterns, url


urlpatterns = patterns(
    'ega.views',
    url(r'^$', 'home', name='home'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^profile/verify/(?P<email>.+)/$', 'verify_email',
        name='verify-email'),

    url(r'^switch/(?P<slug>[\w-]+)/$', 'switch_tournament',
        name='ega-switch-tournament'),

    url(r'^history/$', 'history', name='ega-history'),
    url(r'^invite/$', 'invite_friends', name='ega-invite'),
    url(r'^invite/(?P<league_slug>[\w-]+)/$', 'invite_friends',
        name='ega-invite-league'),
    url(r'^league/$', 'leagues', name='ega-leagues'),
    url(r'^league/(?P<league_slug>[\w-]+)/$', 'league_home',
        name='ega-league-home'),
    url(r'^matches/$', 'next_matches', name='ega-next-matches'),
    url(r'^matches/(?P<match_id>\d+)/$', 'match_details',
        name='ega-match-details'),
    url(r'^ranking/$', 'ranking', name='ega-ranking'),
    url(r'^ranking/f/(?P<round>[\w]+)/$', 'ranking', name='ega-ranking'),
    url(r'^ranking/(?P<league_slug>[\w-]+)/$', 'ranking',
        name='ega-league-ranking'),
    url(r'^ranking/(?P<league_slug>[\w-]+)/f/(?P<round>[\w]+)/$',
        'ranking', name='ega-league-ranking'),
    url(r'^stats/$', 'stats', name='ega-stats'),

    url(r'^join/(?P<slug>[\w-]+)/(?P<key>\w+)/$', 'friend_join',
        name='ega-join'),
    url(r'^join/(?P<slug>[\w-]+)/(?P<key>\w+)/(?P<league_slug>[\w-]+)/$',
        'friend_join', name='ega-join'),
)
