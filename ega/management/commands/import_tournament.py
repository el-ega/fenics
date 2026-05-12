import json

from itertools import combinations

from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from django.utils.timezone import get_default_timezone, make_aware

from ega.models import Match, Team, TeamStats, Tournament


class Command(BaseCommand):
    help = 'Import or update tournament teams and fixtures from JSON.'

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **options):
        try:
            with open(options['path'], encoding='utf-8') as source:
                data = json.load(source)
        except OSError as exc:
            raise CommandError(str(exc))

        tournament_data = data['tournament']
        tournament, _ = Tournament.objects.update_or_create(
            slug=tournament_data['slug'],
            defaults={
                'name': tournament_data['name'],
                'published': tournament_data.get('published', False),
                'finished': tournament_data.get('finished', False),
                'preferences': tournament_data.get('preferences', {}),
            },
        )

        teams_by_code = {}
        for row in data.get('teams', []):
            team, _ = Team.objects.update_or_create(
                slug=row.get('slug') or slugify(row['name']),
                defaults={
                    'name': row['name'],
                    'code': row.get('code', ''),
                    'emoji': row.get('emoji', ''),
                    'image': row.get('image', ''),
                },
            )
            tournament.teams.add(team)
            teams_by_code[team.code or team.slug] = team
            TeamStats.objects.update_or_create(
                tournament=tournament,
                team=team,
                defaults={'zone': row.get('group', '')},
            )

        match_rows = data.get('matches', [])
        if not match_rows and data.get('generate_group_matches'):
            match_rows = _group_matches(
                data.get('teams', []),
                data.get('group_match_schedule', []),
                data.get('group_match_description', 'Grupo {group}'),
            )
        match_rows = match_rows + data.get('playoff_matches', [])

        created = updated = 0
        for row in match_rows:
            home = teams_by_code.get(row.get('home'))
            away = teams_by_code.get(row.get('away'))
            if row.get('home') and home is None:
                raise CommandError('Unknown home team code: %s' % row['home'])
            if row.get('away') and away is None:
                raise CommandError('Unknown away team code: %s' % row['away'])
            when = _parse_when(row.get('when'))
            defaults = {
                'description': row.get('description', ''),
                'home_placeholder': row.get('home_placeholder', ''),
                'away_placeholder': row.get('away_placeholder', ''),
                'when': when,
                'location': row.get('location', ''),
                'knockout': row.get('knockout', False),
                'starred': row.get('starred', False),
            }
            match, was_created = _update_or_create_match(
                tournament=tournament,
                round=row.get('round', ''),
                home=home,
                away=away,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                'Imported %s: %s teams, %s matches created, %s updated'
                % (tournament.slug, tournament.teams.count(), created, updated)
            )
        )


def _parse_when(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise CommandError('Invalid datetime: %s' % value)
    if parsed.tzinfo is None:
        parsed = make_aware(parsed, get_default_timezone())
    return parsed


def _update_or_create_match(tournament, round, home, away, defaults):
    if home and away:
        match = (
            Match.objects.filter(
                tournament=tournament,
                round=round,
                home__in=(home, away),
                away__in=(home, away),
            )
            .exclude(home=models.F('away'))
            .first()
        )
        if match:
            match.home = home
            match.away = away
            match.round = round
            for field, value in defaults.items():
                setattr(match, field, value)
            match.save()
            return match, False

    if home is None and away is None and defaults.get('description'):
        return Match.objects.update_or_create(
            tournament=tournament,
            description=defaults['description'],
            defaults={
                'round': round,
                'home': None,
                'away': None,
                **defaults,
            },
        )

    return Match.objects.update_or_create(
        tournament=tournament,
        round=round,
        home=home,
        away=away,
        defaults=defaults,
    )


def _group_matches(teams, schedule=None, description='Group {group}'):
    groups = {}
    for team in teams:
        groups.setdefault(team.get('group', ''), []).append(team)

    schedule_by_teams = {
        frozenset((row['home'], row['away'])): row for row in schedule or []
    }
    matches = []
    for group, group_teams in sorted(groups.items()):
        if not group:
            continue
        for home, away in combinations(group_teams, 2):
            row = {
                'home': home['code'],
                'away': away['code'],
                'round': group,
                'description': description.format(group=group),
            }
            row.update(
                schedule_by_teams.get(
                    frozenset((home['code'], away['code'])), {}
                )
            )
            matches.append(row)
    return matches
