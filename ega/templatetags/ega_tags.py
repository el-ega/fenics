from django import template
from django.db.models import Count

register = template.Library()


@register.inclusion_tag('ega/_trends.html')
def show_prediction_trends(match):
    """Display a progress bar with prediction trends."""
    trends = match.prediction_set.values('trend').annotate(num=Count('trend'))
    # only consider settled predictions
    total = sum(t['num'] for t in trends if t['trend'])
    values = None
    if total > 0:
        values = {t['trend']: (t['num'] * 100 / total) for t in trends}
    return {'values': values}
