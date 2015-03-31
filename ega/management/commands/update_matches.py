# -*- coding: utf-8 -*-

from datetime import datetime

import demiurge

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import get_default_timezone, make_aware

from ega.constants import DEFAULT_TOURNAMENT
from ega.models import Match, Team, Tournament


TEAM_MAPPING = {
    'Def. y Justicia': 'Defensa y Justicia',
    'Newell`s Old Boys': "Newell's Old Boys",
    'Racing Club': 'Racing',
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
        selector = 'tr.partido'
        base_url = ('http://mundod.lavoz.com.ar/sites/default/files'
                    '/Datafactory/html/v1/primeraa/fixture.html')

    def __unicode__(self):
        return u"%s vs. %s" % (self.home, self.away)

    @property
    def is_finished(self):
        return self.status.lower() == 'finalizado'

    @property
    def when(self):
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
        matches = MatchData.all()
        tournament = Tournament.objects.get(slug=DEFAULT_TOURNAMENT)

        for i, entry in enumerate(matches):
            when = entry.when
            if when.hour != 0:
                changed = False
                home = TEAM_MAPPING.get(entry.home, entry.home)
                away = TEAM_MAPPING.get(entry.away, entry.away)

                home_team = Team.objects.get(name=home)
                away_team = Team.objects.get(name=away)

                match, created = Match.objects.get_or_create(
                    tournament=tournament, home=home_team, away=away_team)

                if created:
                    self.stdout.write(u'Match created: %s\n' % unicode(match))

                if when != match.when:
                    round = (i / 15 + 1)
                    match.when = when
                    match.description = 'Fecha %d' % round
                    match.round = str(round)
                    changed = True

                if (match.home_goals is None or match.away_goals is None) and entry.is_finished:
                    changed = True
                    match.home_goals = entry.home_goals
                    match.away_goals = entry.away_goals
                    self.stdout.write(u'Updated result: %s: %s - %s\n' % (
                        match, entry.home_goals, entry.away_goals))

                if changed:
                    match.save()
