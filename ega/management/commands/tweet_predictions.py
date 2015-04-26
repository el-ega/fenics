# -*- coding: utf-8 -*-

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from TwitterAPI import TwitterAPI

from ega.constants import DEFAULT_TOURNAMENT
from ega.models import Match


class Command(BaseCommand):
    help = 'Tweet admin predictions'

    def handle(self, *args, **options):
        api = TwitterAPI(**settings.TWITTER_CREDENTIALS)
        users = settings.EGA_ADMINS.keys()

        # matches in the last hour
        matches = Match.objects.filter(
            tournament__slug=DEFAULT_TOURNAMENT, when__isnull=False,
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
                    for p in predictions])
                tweet = u"En juego: %s vs %s\n%s" % (
                    m.home.name, m.away.name, data)
                api.request('statuses/update', {'status': tweet})
