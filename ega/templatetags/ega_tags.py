from django import template
from django.db.models import Count

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
        values = {t['trend']: (t['num'] * 100 // total) for t in trends}
        diff = 100 - sum(values.values())
        values[list(values.keys())[-1]] += diff
    return {'home_team': match.home, 'away_team': match.away,
            'count': total, 'values': values}
