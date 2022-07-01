import pygal

from datetime import timedelta

from django import template
from django.db.models import Count
from django.utils.timezone import now
from pygal.style import LightGreenStyle

from ega.constants import NEXT_MATCHES_DAYS
from ega.models import ChampionPrediction, Prediction


register = template.Library()


@register.inclusion_tag('ega/_trends.html')
def show_prediction_trends(match):
    """Display a progress bar with prediction trends."""
    values = None
    # only consider settled predictions
    trends = (
        match.prediction_set.exclude(trend='')
        .values('trend')
        .annotate(num=Count('trend'))
    )
    total = sum(t['num'] for t in trends)
    if total > 0:
        values = {t: 0 for t in ('L', 'E', 'V')}
        for t in trends:
            values[t['trend']] = t['num'] * 100 // total
        diff = 100 - sum(values.values())
        values[list(values.keys())[-1]] += diff

    return {
        'home_team': match.home or match.home_placeholder,
        'away_team': match.away or match.away_placeholder,
        'count': total,
        'values': values,
    }


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
    until = tz_now + timedelta(days=NEXT_MATCHES_DAYS)
    total = tournament.match_set.filter(when__range=(tz_now, until)).count()
    predicted = Prediction.objects.filter(
        home_goals__isnull=False,
        away_goals__isnull=False,
        user=user,
        match__tournament=tournament,
        match__when__range=(tz_now, until),
    ).count()
    return total - predicted


@register.simple_tag
def champion_predictions_chart(tournament):
    data = ChampionPrediction.objects.filter(tournament=tournament).values(
        'team__name'
    )
    data = data.annotate(num=Count('team__name')).order_by('-num')

    font_size = 32
    chart_style = LightGreenStyle(
        legend_font_size=font_size,
        tooltip_font_size=font_size,
        label_font_size=font_size - 10,
        major_label_font_size=font_size,
    )
    max_num = max(data[0]['num'] + 1, 10)
    chart = pygal.HorizontalBar(
        style=chart_style,
        legend_at_bottom=True,
        legend_at_bottom_columns=1,
        range=(1, max_num),
    )
    for e in data[:5]:
        chart.add(e['team__name'], e['num'])

    return chart.render_data_uri()
