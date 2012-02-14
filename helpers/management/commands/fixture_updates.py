# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify

from game.models import Match, MatchGroup, Team, Tournament
from helpers.ole_api import Fixture


class Command(BaseCommand):
    args = '<tournament-slug>'
    help = 'Import fixture and update match info/results'

    def handle(self, *args, **options):
        try:
            t_slug = args[0]
        except IndexError:
            raise CommandError('A tournament slug is required')

        try:
            tournament = Tournament.objects.get(slug=t_slug)
        except Tournament.DoesNotExist:
            tournament = None

        fixture_data = Fixture()

        # create tournament if it does not exist
        if not tournament:
            teams = []
            for team_name in fixture_data.get_teams():
                # create teams if needed
                team, created = Team.objects.get_or_create(
                    name=team_name, slug=slugify(team_name))

                if created:
                    self.stdout.write('Team created: %s\n' %
                                                unicode(team).encode('utf-8'))
                teams.append(team)

            tournament = Tournament(name=u'Primera División', slug=t_slug)
            tournament.save()
            tournament.teams = teams
            tournament.save()

        # check for matches info update
        fecha_nro = 1
        for fecha in fixture_data:
            match_group, created = MatchGroup.objects.get_or_create(
                tournament=tournament, name="Fecha %d" % fecha_nro)

            for partido in fecha:
                home_team = Team.objects.get(name=partido.home_team)
                away_team = Team.objects.get(name=partido.away_team)

                match, created = Match.objects.get_or_create(
                    group=match_group, home=home_team, away=away_team)

                if created:
                    self.stdout.write('Match created: %s\n' %
                                                unicode(match).encode('utf-8'))
                else:
                    self.stdout.write('Match updated: %s\n' %
                                                unicode(match).encode('utf-8'))

                if partido.match_date:
                    match.date = partido.match_date
                    match.referee = partido.referee
                    match.location = partido.stadium

                if partido.status == 'Finalizado':
                    match.home_goals = partido.home_score
                    match.away_goals = partido.away_score

                match.save()

            fecha_nro += 1

