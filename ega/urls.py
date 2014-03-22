from django.conf.urls import patterns, include, url


urlpatterns = patterns(
    'ega.views',
    url(r'^$', 'home', name='home'),
    url(r'^invite/twit/$', 'invite_friends_via_twitter', name='twit'),
)
