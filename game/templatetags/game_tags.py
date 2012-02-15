import datetime

from django import template

from game.models import Match


register = template.Library()


@register.inclusion_tag('game/latest_results.html')
def latest_results(tournament_slug=None, latest=3):
    now = datetime.datetime.now()

    matches = Match.objects.filter(date__lte=now, approved=True
                ).order_by('-date')

    if tournament_slug is not None:
        matches = matches.filter(group__tournament__slug=tournament_slug)

    return {'matches': matches[:latest]}
