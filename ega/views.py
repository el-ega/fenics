import twitter

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from ega.forms import InviteFriendsForm, PredictionForm
from ega.models import Prediction, Tournament


def soon(request):
    return render(request, 'ega/soon.html')


@login_required
def home(request):
    return render(request, 'ega/home.html')


@require_http_methods(('GET', 'POST'))
@login_required
def invite_friends(request):
    can_tweet = request.user.socialaccount_set.filter(
        provider='twitter').exists()

    if request.method == 'POST':
        form = InviteFriendsForm(request.POST)
        if form.is_valid():
            emails = form.cleaned_data['emails']
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            request.user.invite_friends(emails, subject, body)
            if len(emails) > 1:
                msg = '%s amigos invitados!' % len(emails)
            else:
                msg = '1 amigo invitado!'
            messages.success(request, msg)
            return HttpResponseRedirect(reverse('home'))
    else:
        form = InviteFriendsForm()

    return render(
        request, 'ega/invite.html', dict(form=form, tweet=True))  # can_tweet))


@require_http_methods(('GET', 'POST'))
@login_required
def invite_friends_via_email(request):
    if request.method == 'POST':
        form = InviteFriendsForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Friends invited!')
            return HttpResponseRedirect(reverse('home'))
    else:
        form = InviteFriendsForm()

    return render(request, 'ega/invite.html', dict(form=form))


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

    matches = tournament.next_matches()
    # select related positions
    for m in matches:
        # create prediction for user if missing
        Prediction.objects.get_or_create(user=request.user, match=m)
        # get trends (save pred L E V?))

    PredictionFormSet = modelformset_factory(
        Prediction, form=PredictionForm, extra=0)

    if request.method == 'POST':
        formset = PredictionFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(
                reverse('ega-next-matches', args=[slug]))
    else:
        predictions = Prediction.objects.filter(
            user=request.user, match__in=matches)
        formset = PredictionFormSet(queryset=predictions)

    return render(
        request, 'ega/next_matches.html',
        {'tournament': tournament, 'formset': formset})
