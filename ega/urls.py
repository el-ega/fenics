from django.conf.urls import url

import ega.views


urlpatterns = [
    url(r'^$', ega.views.meta_home, name='meta-home'),
    url(r'^logout/$', ega.views.logout, name='logout'),
    url(r'^profile/$', ega.views.profile, name='profile'),
    url(r'^profile/verify/(?P<email>.+)/$', ega.views.verify_email,
        name='verify-email'),

    url(r'^invite/$', ega.views.invite_friends, name='ega-invite'),
    url(r'^(?P<slug>[\w-]+)/invite/(?P<league_slug>[\w-]+)/$',
        ega.views.invite_friends, name='ega-invite-league'),
    url(r'^join/(?P<slug>[\w-]+)/(?P<key>\w+)/$', ega.views.friend_join,
        name='ega-join'),
    url(r'^join/(?P<slug>[\w-]+)/(?P<key>\w+)/(?P<league_slug>[\w-]+)/$',
        ega.views.friend_join, name='ega-join'),

    url(r'^(?P<slug>[\w-]+)/$', ega.views.home, name='ega-home'),
    url(r'^(?P<slug>[\w-]+)/history/$', ega.views.history, name='ega-history'),
    url(r'^(?P<slug>[\w-]+)/league/$', ega.views.leagues, name='ega-leagues'),
    url(r'^(?P<slug>[\w-]+)/league/(?P<league_slug>[\w-]+)/$',
        ega.views.league_home, name='ega-league-home'),
    url(r'^(?P<slug>[\w-]+)/matches/$', ega.views.next_matches,
        name='ega-next-matches'),
    url(r'^(?P<slug>[\w-]+)/matches/(?P<match_id>\d+)/$',
        ega.views.match_details, name='ega-match-details'),
    url(r'^(?P<slug>[\w-]+)/ranking/$', ega.views.ranking, name='ega-ranking'),
    url(r'^(?P<slug>[\w-]+)/ranking/f/(?P<round>[\w]+)/$', ega.views.ranking,
        name='ega-ranking'),
    url(r'^(?P<slug>[\w-]+)/ranking/(?P<league_slug>[\w-]+)/$',
        ega.views.ranking, name='ega-league-ranking'),
    url(r'^(?P<slug>[\w-]+)/ranking/(?P<league_slug>[\w-]+)/f/(?P<round>[\w]+)/$',
        ega.views.ranking, name='ega-league-ranking'),
    url(r'^(?P<slug>[\w-]+)/stats/$', ega.views.stats, name='ega-stats'),

]
