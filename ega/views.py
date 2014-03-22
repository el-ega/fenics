import twitter

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse

from ega.forms import PredictionForm
from ega.models import Prediction, Tournament


@login_required
def home(request):
    can_tweet = request.user.socialaccount_set.filter(
        provider='twitter').exists()
    return render(request, 'ega/home.html', dict(can_tweet=can_tweet))


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
            request, 'We don\'t have your twitter token to tweet for you.')
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

    messages.info(request, 'Tweet successfully posted for you!')
    return HttpResponseRedirect(reverse('home'))


@login_required
def next_matches(request, slug):
    """Return coming matches for the speficied tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)

    # create predictions for user, then get formset
    matches = tournament.next_matches()
    for m in matches:
        Prediction.objects.get_or_create(user=request.user, match=m)
    predictions = Prediction.objects.filter(match__in=matches)

    PredictionFormSet = modelformset_factory(
        Prediction, form=PredictionForm, extra=0)

    if request.method == 'POST':
        formset = PredictionFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(
                reverse('ega-next-matches', args=[slug]))
    else:
        formset = PredictionFormSet(queryset=predictions)

    return render(
        request, 'ega/next_matches.html', {'formset': formset})
