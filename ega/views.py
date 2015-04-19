# -*- coding: utf-8 -*-

from allauth.account.models import EmailAddress
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods

from ega.constants import (
    DEFAULT_TOURNAMENT,
    EXACTLY_MATCH_POINTS,
    INVITE_BODY,
    INVITE_LEAGUE,
    INVITE_SUBJECT,
    RANKING_TEAMS_PER_PAGE,
)
from ega.forms import (
    EgaUserForm,
    InviteFriendsForm,
    LeagueForm,
    PredictionForm,
)
from ega.models import (
    EgaUser,
    League,
    LeagueMember,
    Match,
    Prediction,
    Tournament,
)


def logout(request):
    auth.logout(request)
    messages.success(request, 'Cerraste sesión exitosamente!')
    return HttpResponseRedirect(reverse('home'))


@login_required
def home(request):
    tournament = get_object_or_404(
        Tournament, slug=DEFAULT_TOURNAMENT, published=True)

    matches = tournament.next_matches()
    played = Prediction.objects.filter(user=request.user, match__in=matches,
                                       home_goals__isnull=False,
                                       away_goals__isnull=False)
    pending = matches.count() - played.count()

    current_round = tournament.current_round()
    matches = matches[:3]
    for m in matches:
        try:
            m.user_prediction = played.get(match=m)
        except Prediction.DoesNotExist:
            m.user_prediction = None

    top_ranking = tournament.ranking()[:7]
    history = request.user.history(tournament)[:3]
    stats = request.user.stats(tournament)

    return render(request, 'ega/home.html',
                  {'tournament': tournament, 'top_ranking': top_ranking,
                   'current_round': current_round,
                   'pending': pending, 'matches': matches,
                   'history': history, 'stats': stats})


@require_http_methods(('GET', 'POST'))
@login_required
def profile(request):
    if request.method == 'POST':
        form = EgaUserForm(
            instance=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Perfil actualizado.')
            return HttpResponseRedirect(reverse('profile'))
    else:
        form = EgaUserForm(instance=request.user)
    return render(request, 'ega/profile.html', dict(form=form))


@require_http_methods(('GET', 'POST'))
@login_required
def invite_friends(request, league_slug=None):
    kwargs = dict(key=request.user.invite_key)
    league = None
    if league_slug:
        league = get_object_or_404(
            League, tournament__slug=DEFAULT_TOURNAMENT, slug=league_slug)
        if league.owner != request.user:
            raise Http404
        kwargs['league_slug'] = league.slug
    invite_url = request.build_absolute_uri(reverse('join', kwargs=kwargs))

    if request.method == 'POST':
        form = InviteFriendsForm(request.POST)
        if form.is_valid():
            emails = form.invite(sender=request.user)
            if emails > 1:
                msg = '%s amigos invitados!' % emails
            else:
                msg = '1 amigo invitado!'
            messages.success(request, msg)
            return HttpResponseRedirect(reverse('home'))
    else:
        subject = INVITE_SUBJECT
        extra_text = ''
        if league:
            subject += ', jugando en mi liga de amigos %s' % league.name
            extra_text = INVITE_LEAGUE % dict(league_name=league.name)

        initial = dict(
            subject=subject,
            body=INVITE_BODY % dict(
                extra_text=extra_text, url=invite_url,
                inviter=request.user.visible_name()),
        )
        form = InviteFriendsForm(initial=initial)

    return render(request, 'ega/invite.html',
                  dict(form=form, league=league, invite_url=invite_url))


@require_GET
@login_required
def friend_join(request, key, league_slug=None):
    get_object_or_404(EgaUser, invite_key=key)

    if league_slug:
        league = get_object_or_404(
            League, tournament__slug=DEFAULT_TOURNAMENT, slug=league_slug)
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
            league = form.save()
            LeagueMember.objects.create(
                user=request.user, league=league, is_owner=True)
            return HttpResponseRedirect(
                reverse('invite-league', kwargs=dict(league_slug=league.slug)))
    else:
        form = LeagueForm()
    leagues = League.objects.current().filter(members=request.user)
    return render(
        request, 'ega/leagues.html', dict(leagues=leagues, form=form))


@require_GET
@login_required
def league_home(request, slug, league_slug):
    tournament = get_object_or_404(Tournament, slug=slug, published=True)
    league = get_object_or_404(
        League, tournament=tournament, slug=league_slug, members=request.user)

    top_ranking = league.ranking()[:5]
    stats = request.user.stats(tournament)

    return render(request, 'ega/league_home.html',
                  {'tournament': tournament, 'league': league,
                   'top_ranking': top_ranking, 'stats': stats})


@login_required
def next_matches(request, slug):
    """Return coming matches for the specified tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)

    matches = tournament.next_matches()
    for m in matches:
        # create prediction for user if missing
        Prediction.objects.get_or_create(
            user=request.user, match=m, defaults={'starred': m.starred})

    PredictionFormSet = modelformset_factory(
        Prediction, form=PredictionForm, extra=0)
    predictions = Prediction.objects.filter(
        user=request.user, match__in=matches)

    if request.method == 'POST':
        formset = PredictionFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Pronósticos actualizados.')

            expired_matches = [f.instance.match for f in formset if f.expired]
            for m in expired_matches:
                msg = "%s - %s: el partido expiró, pronóstico NO actualizado."
                messages.error(request, msg % (m.home.name, m.away.name))

            return HttpResponseRedirect(
                reverse('ega-next-matches', args=[slug]))

    else:
        formset = PredictionFormSet(queryset=predictions)

    return render(
        request, 'ega/next_matches.html',
        {'tournament': tournament, 'formset': formset})


@login_required
def match_details(request, slug, match_id):
    """Return specified match stats."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)
    match = get_object_or_404(Match, id=match_id, tournament=tournament)

    exacts = Prediction.objects.none()
    winners = Prediction.objects.none()
    finished = match.home_goals is not None and match.away_goals is not None
    if finished:
        winners = Prediction.objects.filter(
            match=match, score__gt=0, score__lt=EXACTLY_MATCH_POINTS)
        exacts = Prediction.objects.filter(
            match=match, score__gte=EXACTLY_MATCH_POINTS
        ).select_related('user')

    return render(
        request, 'ega/match_details.html',
        {'tournament': tournament, 'match': match,
         'finished': finished, 'exacts': exacts, 'winners': winners})


@login_required
def ranking(request, slug, league_slug=None, round=None):
    """Return ranking and stats for the specified tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)
    league = None

    base_url = reverse('ega-ranking', args=[slug])
    if league_slug is not None:
        base_url = reverse('ega-league-ranking', args=[slug, league_slug])
        league = get_object_or_404(
            League, tournament=tournament, slug=league_slug)

    user = request.user
    scores = (league.ranking(round=round)
              if league else tournament.ranking(round=round))
    try:
        position = ([r['username'] for r in scores]).index(user.username)
        position += 1
    except ValueError:
        position = None
    paginator = Paginator(scores, RANKING_TEAMS_PER_PAGE)

    page = request.GET.get('page')
    try:
        ranking = paginator.page(page)
    except PageNotAnInteger:
        ranking = paginator.page(1)
    except EmptyPage:
        ranking = paginator.page(paginator.num_pages)

    stats = user.stats(tournament, round=round)
    round_choices = tournament.match_set.filter(
        home_goals__isnull=False, away_goals__isnull=False).values_list(
        'round', flat=True).order_by('round').distinct()

    return render(
        request, 'ega/ranking.html',
        {'tournament': tournament, 'league': league,
         'base_url': base_url, 'round': round, 'choices': round_choices,
         'ranking': ranking, 'user_position': position, 'stats': stats})


@login_required
def history(request, slug):
    """Return history for the specified tournament."""
    tournament = get_object_or_404(Tournament, slug=slug, published=True)

    user_history = request.user.history(tournament)
    paginator = Paginator(user_history, RANKING_TEAMS_PER_PAGE)

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


@login_required
def verify_email(request, email):
    email_address = get_object_or_404(
        EmailAddress, user=request.user, email=email)
    email_address.send_confirmation(request)
    messages.success(request, 'Email de verificación enviado a %s' % email)
    return HttpResponseRedirect(reverse('profile'))
