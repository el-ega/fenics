from django import template
from django.db.models import Count, Q
from django.utils.timezone import now

from ega.models import Prediction


register = template.Library()


@register.inclusion_tag('ega/_trends.html')
def show_prediction_trends(match):
    """Display a progress bar with prediction trends."""
    values = None
    # only consider settled predictions
    trends = match.prediction_set.exclude(
        trend='').values('trend').annotate(num=Count('trend'))
    total = sum(t['num'] for t in trends)
    if total > 0:
        values = {t: 0 for t in ('L', 'E', 'V')}
        for t in trends:
            values[t['trend']] = t['num'] * 100 // total
        diff = 100 - sum(values.values())
        values[list(values.keys())[-1]] += diff

    return {'home_team': match.home or match.home_placeholder,
            'away_team': match.away or match.away_placeholder,
            'count': total, 'values': values}


@register.simple_tag
def get_friends_leagues(user, slug):
    return user.league_set.filter(tournament__slug=slug)


@register.simple_tag
def get_latest_matches(team, tournament):
    if team is None:
        return None
    return team.latest_matches(tournament)


@register.simple_tag
def get_user_stats(user, tournament):
    return user.stats(tournament)


@register.simple_tag
def get_pending_predictions(user, tournament):
    tz_now = now()
    return Prediction.objects.filter(
        Q(home_goals__isnull=True) | Q(away_goals__isnull=True),
        user=user, match__tournament=tournament,
        match__when__gt=tz_now).count()
