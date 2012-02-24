from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.forms.models import modelformset_factory
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from forms import BaseCardForm, BaseCardFormSet
from models import Tournament, Card, Match, TeamPosition


@login_required
def pending_matches(request):
    saved = False
    tournament = Tournament.objects.all()[0]
    CardFormSet = modelformset_factory(Card, form=BaseCardForm,
                                       formset=BaseCardFormSet, extra=0)
    if request.method == 'POST':
        formset = CardFormSet(request.user, tournament, request.POST)
        if formset.is_valid():
            formset.save()
            saved = True
    else:
        formset = CardFormSet(request.user, tournament)

    return render_to_response('game/pending_matches.html',
                              {'formset': formset, 'saved': saved},
                              context_instance=RequestContext(request))

@login_required
def tournament_standings(request, tournament='primera-division'):
    standings = TeamPosition.objects.filter(tournament__slug=tournament)
    return render_to_response('game/tournament_standings.html',
                              {'standings': standings},
                              context_instance=RequestContext(request))

@login_required
def match_info(request):
    match_id = request.POST.get('match_id', 0)
    match = get_object_or_404(Match, id=match_id)

    cards = match.card_set.all()
    total_cards = cards.count()
    home_cards = cards.filter(home_goals__gt=F('away_goals')).count()
    away_cards = cards.filter(home_goals__lt=F('away_goals')).count()
    home_percentage = 100.0 * home_cards / total_cards
    away_percentage = 100.0 * away_cards / total_cards
    tie_percentage = 100.0 - (home_percentage + away_percentage)
    
    return render_to_response('game/match_info.html',
                              {'match': match,
                               'home_percentage': home_percentage,
                               'tie_percentage': tie_percentage,
                               'away_percentage': away_percentage},
                              context_instance=RequestContext(request))
