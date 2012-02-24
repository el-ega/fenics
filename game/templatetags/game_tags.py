import datetime

from django import template

from game.models import Match, TeamPosition


register = template.Library()


@register.inclusion_tag('game/latest_results.html')
def latest_results(tournament=None, latest=3):
    now = datetime.datetime.now()

    matches = Match.objects.filter(date__lte=now, approved=True
                ).order_by('-date')

    if tournament is not None:
        matches = matches.filter(group__tournament=tournament)

    return {'matches': matches[:latest]}


@register.inclusion_tag('game/team_position.html')
def team_position(tournament, team):
    try:
        position = TeamPosition.objects.get(tournament=tournament, team=team)
    except TeamPosition.DoesNotExist:
        position = None
    return {'position': position}
