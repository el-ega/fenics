from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('game.views',
    url(r'^pending/$', 'pending_matches', name='game-pending-matches'),
    url(r'^standings/$', 'tournament_standings', name='game-tournament-standings'),
    url(r'^match-info/$', 'match_info', name='game-match-info'),
)
