from django.conf.urls import patterns, url


urlpatterns = patterns(
    'ega.views',
    url(r'^$', 'home', name='home'),
    url(r'^invite/$', 'invite_friends', name='invite'),
    url(r'^invite/email/$', 'invite_friends_via_email', name='invite-email'),
    url(r'^invite/tweet/$', 'invite_friends_via_twitter', name='invite-tweet'),
    url(r'^(?P<slug>[\w-]+)/matches/$', 'next_matches',
        name='ega-next-matches'),
)
