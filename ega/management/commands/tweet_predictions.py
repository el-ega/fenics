# -*- coding: utf-8 -*-

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from TwitterAPI import TwitterAPI

from ega.models import Match, Prediction


PREDICTION_COUNT_QUERY = """
    SELECT *, COUNT(*) AS count FROM ega_prediction
    WHERE match_id=%s AND home_goals IS NOT NULL AND away_goals IS NOT NULL
    GROUP BY home_goals, away_goals ORDER BY count DESC
"""


class Command(BaseCommand):
    help = 'Tweet admin predictions and predictions count'

    def handle(self, *args, **options):
        api = TwitterAPI(**settings.TWITTER_CREDENTIALS)
        users = settings.EGA_ADMINS.keys()

        # matches in the last hour
        matches = Match.objects.filter(
            when__isnull=False,
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
            counts = Prediction.objects.raw(
                PREDICTION_COUNT_QUERY, params=[m.id])
            preds = '\n'.join([
                '#%s %d - %d #%s (%d)' % (r.match.home.code,
                                          r.home_goals, r.away_goals,
                                          r.match.away.code, r.count)
                for r in counts[:3]
            ])
            tweet = 'Los resultados más pronosticados:\n' + preds
            api.request('statuses/update', {'status': tweet})
