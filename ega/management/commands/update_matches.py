# -*- coding: utf-8 -*-

from datetime import datetime

import demiurge

from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone, make_aware

from ega.models import Match, Team, Tournament


TEAM_MAPPING = {
    'Def. y Justicia': 'Defensa y Justicia',
    'Newell`s': "Newell's Old Boys",
    'Racing Club': 'Racing',
    'Talleres': 'Talleres (Cba)',
    'Atl. Rafaela': 'Atlético Rafaela',
}


class MatchData(demiurge.Item):
    home = demiurge.TextField(selector='td.equipo:eq(0)')
    away = demiurge.TextField(selector='td.equipo:eq(1)')
    home_goals = demiurge.TextField(selector='td.gol.loc')
    away_goals = demiurge.TextField(selector='td.gol.vis')
    status = demiurge.TextField(selector='td.estado')
    _date = demiurge.TextField(selector='td.dia')
    _time = demiurge.TextField(selector='td.hora')

    class Meta:
        selector = '#fase_n1 tr.partido'
        base_url = ('http://mundod.lavoz.com.ar/sites/default/files'
                    '/Datafactory/html/v1/primeraa/fixture.html')

    def __str__(self):
        return u"%s vs. %s" % (self.home, self.away)

    @property
    def is_finished(self):
        return self.status.lower() == 'finalizado'

    @property
    def is_suspended(self):
        return self.status.lower() == 'suspendido'

    @property
    def when(self):
        if self._time is None:
            return None

        if self._time.startswith('-'):
            match_time = "00:00"
        else:
            match_time = self._time[:5]

        date_and_time = "%s %s" % (self._date, match_time)
        value = datetime.strptime(date_and_time, "%d-%m-%Y %H:%M")
        return make_aware(value, get_default_timezone())


class Command(BaseCommand):
    help = 'Import match details'

    def handle(self, *args, **options):
        try:
            matches = MatchData.all()
        except:
            # skip if couldn't get data
            return

        tournament = Tournament.objects.get(slug='superliga')

        for i, entry in enumerate(matches):
            when = entry.when
            changed = False

            home = TEAM_MAPPING.get(entry.home, entry.home)
            away = TEAM_MAPPING.get(entry.away, entry.away)

            home_team = Team.objects.get(
                name=home, tournament=tournament)
            away_team = Team.objects.get(
                name=away, tournament=tournament)

            match, created = Match.objects.get_or_create(
                tournament=tournament, home=home_team, away=away_team)

            if created:
                self.stdout.write(u'Match created: %s\n' % str(match))

            if not match.suspended and entry.is_suspended:
                match.suspended = True
                changed = True

            if when != match.when and not match.suspended and when.hour != 0:
                round = (i // 14 + 1)
                match.when = when
                match.description = 'Fecha %d' % round
                match.round = str(round)
                changed = True

            if not match.finished and entry.home_goals != '' and entry.away_goals != '':
                changed = True
                match.home_goals = entry.home_goals
                match.away_goals = entry.away_goals
                match.finished = entry.is_finished
                if match.finished:
                    self.stdout.write(u'Updated result: %s: %s - %s\n' % (
                        match, entry.home_goals, entry.away_goals))

            if changed:
                match.save()
