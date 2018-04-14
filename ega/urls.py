from django.urls import path

import ega.views


urlpatterns = [
    path('', ega.views.meta_home, name='meta-home'),
    path('logout/', ega.views.logout, name='logout'),
    path('profile/', ega.views.profile, name='profile'),
    path('profile/verify/<str:email>/', ega.views.verify_email,
         name='verify-email'),

    path('invite/', ega.views.invite_friends, name='ega-invite'),
    path('<slug:slug>/invite/<slug:league_slug>/',
         ega.views.invite_friends, name='ega-invite-league'),
    path('join/<slug:slug>/<str:key>/', ega.views.friend_join,
         name='ega-join'),
    path('join/<slug:slug>/<str:key>/<slug:league_slug>/',
         ega.views.friend_join, name='ega-join'),

    path('<slug:slug>/', ega.views.home, name='ega-home'),
    path('<slug:slug>/update-champion', ega.views.update_champion_prediction,
         name='ega-update-champion'),
    path('<slug:slug>/history/', ega.views.history, name='ega-history'),
    path('<slug:slug>/league/', ega.views.leagues, name='ega-leagues'),
    path('<slug:slug>/league/<slug:league_slug>/',
         ega.views.league_home, name='ega-league-home'),
    path('<slug:slug>/matches/', ega.views.next_matches,
         name='ega-next-matches'),
    path('<slug:slug>/matches/<int:match_id>/',
         ega.views.match_details, name='ega-match-details'),
    path('<slug:slug>/ranking/', ega.views.ranking, name='ega-ranking'),
    path('<slug:slug>/ranking/f/<str:round>/', ega.views.ranking,
         name='ega-ranking'),
    path('<slug:slug>/ranking/<slug:league_slug>/',
         ega.views.ranking, name='ega-league-ranking'),
    path('<slug:slug>/ranking/<slug:league_slug>/f/<str:round>/',
         ega.views.ranking, name='ega-league-ranking'),
    path('<slug:slug>/stats/', ega.views.stats, name='ega-stats'),
]
