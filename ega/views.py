import twitter

from allauth.account.forms import LoginForm, SignupForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_http_methods

from ega.constants import RANKING_TEAMS_PER_PAGE
from ega.forms import InviteFriendsForm, LeagueForm, PredictionForm
from ega.models import EgaUser, League, LeagueMember, Prediction, Tournament


def get_absolute_url(url):
    return Site.objects.get_current().domain + url


@login_required
def home(request):
    tournament = get_object_or_404(
        Tournament, slug=game_settings.DEFAULT_TOURNAMENT, published=True)

    top_ranking = tournament.ranking()[:10]
    matches = tournament.next_matches()[:3]
    history = request.user.history(tournament)[:3]
    stats = request.user.stats(tournament)

    return render(request, 'ega/home.html',
                  {'tournament': tournament, 'top_ranking': top_ranking,
                   'matches': matches, 'history': history, 'stats': stats})


@require_http_methods(('GET', 'POST'))
@login_required
def invite_friends(request, league_slug=None):
    kwargs = dict(key=request.user.invite_key)
    league = None
    if league_slug:
        league = get_object_or_404(League, slug=league_slug)
        kwargs['league_slug'] = league.slug

    invite_url = get_absolute_url(reverse('join', kwargs=kwargs))
    if request.method == 'POST':
        form = InviteFriendsForm(invite_url, request.POST)
        if form.is_valid():
            emails = form.invite(sender=request.user)
            if emails > 1:
                msg = '%s amigos invitados!' % emails
            else:
                msg = '1 amigo invitado!'
            messages.success(request, msg)
            return HttpResponseRedirect(reverse('home'))
    else:
        form = InviteFriendsForm(invite_url)

    return render(request, 'ega/invite.html', dict(form=form, league=league))


@require_GET
@login_required
def friend_join(request, key, league_slug=None):
    friend = get_object_or_404(EgaUser, invite_key=key)

    if league_slug:
        league = get_object_or_404(League, slug=league_slug)
        member, created = LeagueMember.objects.get_or_create(
            user=request.user, league=league)
        if created:
            messages.success(
                request, 'Te uniste a el Ega, en la liga %s!' % league)
        else:
            messages.warning(request, 'Ya sos miembro de la liga %s.' % league)
    else:
        messages.success(request, 'Te uniste a el Ega!')
    return HttpResponseRedirect(reverse('home'))


@require_http_methods(('GET', 'POST'))
@login_required
def leagues(request):
    if request.method == 'POST':
        form = LeagueForm(request.POST)
        if form.is_valid():
            league = form.save(commit=False)
            league.slug = slugify(league.name)
            league.save()
            LeagueMember.objects.create(
                user=request.user, league=league, is_owner=True)
            return HttpResponseRedirect(
                reverse('invite-league', kwargs=dict(league_slug=league.slug)))
    else:
        form = LeagueForm()
    leagues = League.objects.filter(members=request.user)
    return render(
        request, 'ega/leagues.html', dict(leagues=leagues, form=form))


@login_required
def next_matches(request, slug):
    """Return coming matches for the specified tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)

    matches = tournament.next_matches()
    for m in matches:
        # create prediction for user if missing
        Prediction.objects.get_or_create(user=request.user, match=m)

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


@login_required
def ranking(request, slug):
    """Return ranking and stats for the specified tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)

    scores = tournament.ranking()
    paginator = Paginator(scores, RANKING_TEAMS_PER_PAGE)

    page = request.GET.get('page')
    try:
        ranking = paginator.page(page)
    except PageNotAnInteger:
        ranking = paginator.page(1)
    except EmptyPage:
        ranking = paginator.page(paginator.num_pages)

    stats = request.user.stats(tournament)

    return render(
        request, 'ega/ranking.html',
        {'tournament': tournament, 'ranking': ranking, 'stats': stats})


@login_required
def history(request, slug):
    """Return history for the specified tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)

    user_history = request.user.history(tournament)
    paginator = Paginator(user_history, game_settings.RANKING_TEAMS_PER_PAGE)

    page = request.GET.get('page')
    try:
        predictions = paginator.page(page)
    except PageNotAnInteger:
        predictions = paginator.page(1)
    except EmptyPage:
        predictions = paginator.page(paginator.num_pages)

    stats = request.user.stats(tournament)

    return render(
        request, 'ega/history.html',
        {'tournament': tournament, 'predictions': predictions, 'stats': stats})
