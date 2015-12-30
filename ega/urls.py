from django.conf.urls import url

import ega.views


urlpatterns = [
    url(r'^$', ega.views.home, name='home'),
    url(r'^logout/$', ega.views.logout, name='logout'),
    url(r'^profile/$', ega.views.profile, name='profile'),
    url(r'^profile/verify/(?P<email>.+)/$', ega.views.verify_email,
        name='verify-email'),

    url(r'^switch/(?P<slug>[\w-]+)/$', ega.views.switch_tournament,
        name='ega-switch-tournament'),

    url(r'^history/$', ega.views.history, name='ega-history'),
    url(r'^invite/$', ega.views.invite_friends, name='ega-invite'),
    url(r'^invite/(?P<league_slug>[\w-]+)/$', ega.views.invite_friends,
        name='ega-invite-league'),
    url(r'^league/$', ega.views.leagues, name='ega-leagues'),
    url(r'^league/(?P<league_slug>[\w-]+)/$', ega.views.league_home,
        name='ega-league-home'),
    url(r'^matches/$', ega.views.next_matches, name='ega-next-matches'),
    url(r'^matches/(?P<match_id>\d+)/$', ega.views.match_details,
        name='ega-match-details'),
    url(r'^ranking/$', ega.views.ranking, name='ega-ranking'),
    url(r'^ranking/f/(?P<round>[\w]+)/$', ega.views.ranking,
        name='ega-ranking'),
    url(r'^ranking/(?P<league_slug>[\w-]+)/$', ega.views.ranking,
        name='ega-league-ranking'),
    url(r'^ranking/(?P<league_slug>[\w-]+)/f/(?P<round>[\w]+)/$',
        ega.views.ranking, name='ega-league-ranking'),
    url(r'^stats/$', ega.views.stats, name='ega-stats'),

    url(r'^join/(?P<slug>[\w-]+)/(?P<key>\w+)/$', ega.views.friend_join,
        name='ega-join'),
    url(r'^join/(?P<slug>[\w-]+)/(?P<key>\w+)/(?P<league_slug>[\w-]+)/$',
        ega.views.friend_join, name='ega-join'),
]
