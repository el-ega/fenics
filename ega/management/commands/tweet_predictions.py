# -*- coding: utf-8 -*-

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.timezone import now
from TwitterAPI import TwitterAPI

from ega.models import Match


PREDICTION_COUNT_QUERY = """
    SELECT home_goals, away_goals, COUNT(*) AS count FROM ega_prediction
    WHERE match_id=%s AND home_goals IS NOT NULL AND away_goals IS NOT NULL
    GROUP BY home_goals, away_goals ORDER BY count DESC LIMIT %s
"""


def get_top_predictions(match, top=3):
    """Return the most common predictions for given match."""
    cursor = connection.cursor()

    cursor.execute(PREDICTION_COUNT_QUERY, [match.id, top])
    rows = cursor.fetchall()
    return rows


class Command(BaseCommand):
    help = 'Tweet admin predictions and predictions count'

    def handle(self, *args, **options):
        api = TwitterAPI(**settings.TWITTER_CREDENTIALS)
        users = settings.EGA_ADMINS.keys()

        # matches in the last hour
        matches = Match.objects.filter(
            when__isnull=False, suspended=False,
            when__range=(now() - timedelta(minutes=30), now()))

        for m in matches:
            predictions = m.prediction_set.filter(
                user__username__in=users).order_by('user')
            if predictions:
                data = ', '.join([
                    "%s dice %s %d-%d %s" % (
                        settings.EGA_ADMINS[p.user.username],
                        m.home.code, p.home_goals,
                        p.away_goals, m.away.code)
                    for p in predictions
                    if p.home_goals is not None and p.away_goals is not None])
                tweet = u"En juego: %s vs %s\n%s" % (
                    m.home.name, m.away.name, data)
                api.request('statuses/update', {'status': tweet})

            # get predictions count and tweet
            counts = get_top_predictions(m)
            preds = '\n'.join([
                '#%s %d - %d #%s (%d)' % (m.home.code, r[0], r[1],
                                          m.away.code, r[2])
                for r in counts
            ])
            tweet = 'Los resultados más pronosticados:\n' + preds
            api.request('statuses/update', {'status': tweet})
