import twitter

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import Http404, HttpResponseRedirect
from django.shortcuts import render


@login_required
def home(request):
    can_twit = request.user.socialaccount_set.filter(
        provider='twitter').exists()
    return render(request, 'ega/home.html', dict(can_twit=can_twit))


@login_required
def invite_friends_via_twitter(request):
    twitter_account = request.user.socialaccount_set.filter(
        provider='twitter')
    if not twitter_account:
        return Http404

    twitter_account = twitter_account[0]
    # XXX: filter by non-expired creds
    creds = twitter_account.socialtoken_set.all()
    if not creds:
        messages.warning(
            request, 'We don\'t have your twitter token to twit for you.')
        return HttpResponseRedirect(reverse('home'))

    creds = creds[0]

    consumer = creds.app
    assert consumer.provider == 'twitter'
    api = twitter.Api(
        consumer_key=consumer.client_id, consumer_secret=consumer.secret,
        access_token_key=creds.token, access_token_secret=creds.token_secret,
    )

    api.PostUpdate(
        'Come and join me at "el Ega" for the WorldCup 2014! '
        'Visit http://el-ega.com.ar'
    )

    messages.info(request, 'Twit successfully posted for you!')
    return HttpResponseRedirect(reverse('home'))
