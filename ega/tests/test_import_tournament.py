import json
import tempfile

from zoneinfo import ZoneInfo

from django.core.management import call_command

from ega.models import Match, Team, TeamStats, Tournament
from ega.tests.helpers import TestCase


class ImportTournamentTestCase(TestCase):
    def test_import_is_idempotent(self):
        data = {
            'tournament': {
                'name': 'World Cup 2026',
                'slug': 'worldcup-2026',
                'published': True,
            },
            'teams': [
                {
                    'name': 'Mexico',
                    'code': 'MEX',
                    'group': 'A',
                    'emoji': '🇲🇽',
                    'image': 'teams/flags/MEX.png',
                },
                {'name': 'South Africa', 'code': 'RSA', 'group': 'A'},
            ],
            'matches': [
                {
                    'home': 'MEX',
                    'away': 'RSA',
                    'round': '1',
                    'description': 'Group A',
                    'when': '2026-06-11T20:00:00-03:00',
                    'location': 'Mexico City Stadium',
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp:
            json.dump(data, tmp)
            tmp.flush()
            call_command('import_tournament', tmp.name)
            call_command('import_tournament', tmp.name)

        tournament = Tournament.objects.get(slug='worldcup-2026')
        self.assertTrue(tournament.published)
        mexico = Team.objects.get(code='MEX')
        self.assertEqual(mexico.emoji, '🇲🇽')
        self.assertEqual(mexico.image.name, 'teams/flags/MEX.png')
        self.assertEqual(
            Match.objects.filter(tournament=tournament).count(), 1
        )
        self.assertEqual(
            TeamStats.objects.get(
                tournament=tournament, team__code='MEX'
            ).zone,
            'A',
        )

    def test_generated_group_matches_use_optional_schedule(self):
        data = {
            'tournament': {
                'name': 'World Cup 2026',
                'slug': 'worldcup-2026',
            },
            'generate_group_matches': True,
            'group_match_schedule': [
                {
                    'home': 'MEX',
                    'away': 'RSA',
                    'when': '2026-06-11T16:00:00-03:00',
                    'location': 'Mexico City Stadium',
                }
            ],
            'teams': [
                {'name': 'Mexico', 'code': 'MEX', 'group': 'A'},
                {'name': 'South Africa', 'code': 'RSA', 'group': 'A'},
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp:
            json.dump(data, tmp)
            tmp.flush()
            call_command('import_tournament', tmp.name)

        match = Match.objects.get()
        self.assertEqual(match.location, 'Mexico City Stadium')
        when = match.when.astimezone(
            ZoneInfo('America/Argentina/Buenos_Aires')
        )
        self.assertEqual(when.isoformat(), '2026-06-11T16:00:00-03:00')

    def test_generated_group_matches_use_description_template(self):
        data = {
            'tournament': {
                'name': 'Mundial 2026',
                'slug': 'mundial-2026',
            },
            'generate_group_matches': True,
            'group_match_description': 'Grupo {group}',
            'teams': [
                {'name': 'México', 'code': 'MEX', 'group': 'A'},
                {'name': 'Sudáfrica', 'code': 'RSA', 'group': 'A'},
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp:
            json.dump(data, tmp)
            tmp.flush()
            call_command('import_tournament', tmp.name)

        self.assertEqual(Match.objects.get().description, 'Grupo A')

    def test_imports_playoff_matches_with_placeholders(self):
        data = {
            'tournament': {
                'name': 'World Cup 2026',
                'slug': 'worldcup-2026',
            },
            'teams': [],
            'playoff_matches': [
                {
                    'description': 'Match 73 - Round of 32',
                    'round': 'Round of 32',
                    'home_placeholder': '2A',
                    'away_placeholder': '2B',
                    'when': '2026-06-28T16:00:00-03:00',
                    'location': 'Los Angeles Stadium',
                    'knockout': True,
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp:
            json.dump(data, tmp)
            tmp.flush()
            call_command('import_tournament', tmp.name)
            call_command('import_tournament', tmp.name)

        self.assertEqual(Match.objects.count(), 1)
        match = Match.objects.get()
        self.assertTrue(match.knockout)
        self.assertIsNone(match.home)
        self.assertIsNone(match.away)
        self.assertEqual(match.home_placeholder, '2A')
        self.assertEqual(match.away_placeholder, '2B')
        self.assertEqual(match.location, 'Los Angeles Stadium')
