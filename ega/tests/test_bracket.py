from ega.bracket import (
    build_predicted_standings,
    projected_bracket,
    projected_bracket_rounds,
    projected_bracket_share_text,
)
from ega.tests.helpers import TestCase


class WorldCupBracketTestCase(TestCase):
    def test_predicted_standings_include_best_third_places(self):
        tournament = self.factory.make_tournament(slug='worldcup-2026')
        teams = {}
        for zone in ('A', 'B', 'C'):
            teams[zone] = [self.factory.make_team() for i in range(4)]
            for team in teams[zone]:
                tournament.teams.add(team)
                team.teamstats_set.get_or_create(
                    tournament=tournament, defaults={'zone': zone}
                )

        user = self.factory.make_user()
        predictions = []
        for zone, group in teams.items():
            predictions.extend(
                [
                    self.factory.make_prediction(
                        user=user,
                        match=self.factory.make_match(
                            tournament=tournament,
                            home=group[0],
                            away=group[1],
                            knockout=False,
                        ),
                        home_goals=3,
                        away_goals=0,
                    ),
                    self.factory.make_prediction(
                        user=user,
                        match=self.factory.make_match(
                            tournament=tournament,
                            home=group[2],
                            away=group[3],
                            knockout=False,
                        ),
                        home_goals=1,
                        away_goals=0,
                    ),
                    self.factory.make_prediction(
                        user=user,
                        match=self.factory.make_match(
                            tournament=tournament,
                            home=group[1],
                            away=group[2],
                            knockout=False,
                        ),
                        home_goals=2,
                        away_goals=1,
                    ),
                ]
            )

        standings, third_places = build_predicted_standings(
            tournament, predictions
        )

        self.assertEqual(standings['1A'], teams['A'][0].id)
        self.assertEqual(standings['2A'], teams['A'][2].id)
        self.assertEqual(standings['3A'], teams['A'][1].id)
        self.assertEqual(
            [row['label'] for row in third_places], ['3C', '3B', '3A']
        )

    def test_projected_bracket_resolves_slots(self):
        tournament = self.factory.make_tournament(slug='worldcup-2026')
        user = self.factory.make_user()
        team_1a = self.factory.make_team(name='Mexico', code='MEX')
        team_3c = self.factory.make_team(name='Haiti', code='HAI')
        tournament.teams.add(team_1a, team_3c)
        user.preferences['predicted_ranking'] = {
            'version': 2,
            'standings': {'1A': team_1a.id, '3C': team_3c.id},
            'third_places': [
                {
                    'label': '3C',
                    'team_id': team_3c.id,
                    'zone': 'C',
                    'points': 4,
                    'goal_difference': 1,
                    'goals_for': 3,
                }
            ],
        }

        bracket = projected_bracket(tournament, user)

        self.assertEqual(bracket[1]['away'], team_3c)
        self.assertEqual(bracket[6]['home'], team_1a)

    def test_projected_bracket_uses_third_place_teams_once(self):
        tournament = self.factory.make_tournament(slug='worldcup-2026')
        user = self.factory.make_user()
        teams = {
            '3C': self.factory.make_team(name='Haiti', code='HAI'),
            '3E': self.factory.make_team(name='Qatar', code='QAT'),
        }
        tournament.teams.add(*teams.values())
        user.preferences['predicted_ranking'] = {
            'version': 2,
            'standings': {},
            'third_places': [
                {
                    'label': '3C',
                    'team_id': teams['3C'].id,
                    'zone': 'C',
                    'points': 4,
                    'goal_difference': 1,
                    'goals_for': 3,
                },
                {
                    'label': '3E',
                    'team_id': teams['3E'].id,
                    'zone': 'E',
                    'points': 4,
                    'goal_difference': 0,
                    'goals_for': 2,
                },
            ],
        }

        bracket = projected_bracket(tournament, user)
        third_place_teams = [
            side
            for match in bracket
            if match['round'] == 'Round of 32'
            for side in (match['home'], match['away'])
            if side in teams.values()
        ]

        self.assertEqual(third_place_teams.count(teams['3C']), 1)
        self.assertEqual(third_place_teams.count(teams['3E']), 1)

    def test_projected_bracket_rounds_are_ordered_by_topology(self):
        tournament = self.factory.make_tournament(slug='worldcup-2026')
        user = self.factory.make_user()

        rounds = projected_bracket_rounds(tournament, user)
        round32 = rounds[0]['matches']
        round16 = rounds[1]['matches']

        self.assertEqual(
            [match['match'] for match in round32[:4]], [74, 77, 73, 75]
        )
        self.assertEqual([match['match'] for match in round16[:2]], [89, 90])

    def test_projected_bracket_share_text_is_tweet_sized(self):
        tournament = self.factory.make_tournament(
            preferences={
                'format': {
                    'bracket': (
                        {
                            'match': 1,
                            'round': 'Semi-final',
                            'home': '1A',
                            'away': '2A',
                        },
                        {
                            'match': 2,
                            'round': 'Semi-final',
                            'home': '1B',
                            'away': '2B',
                        },
                        {
                            'match': 3,
                            'round': 'Final',
                            'home': 'W1',
                            'away': 'W2',
                        },
                    )
                }
            }
        )
        user = self.factory.make_user()
        teams = {
            slot: self.factory.make_team(
                name=slot, code=slot, emoji='🇺🇾'
            )
            for slot in ('1A', '2A', '1B', '2B')
        }
        tournament.teams.add(*teams.values())
        user.preferences['predicted_ranking'] = {
            'version': 2,
            'standings': {
                slot: team.id for slot, team in teams.items()
            },
        }
        user.save(update_fields=['preferences'])
        match1 = self.factory.make_match(
            tournament=tournament,
            home=None,
            away=None,
            description='Match 1 - Semi-final',
            knockout=True,
        )
        match2 = self.factory.make_match(
            tournament=tournament,
            home=None,
            away=None,
            description='Match 2 - Semi-final',
            knockout=True,
        )
        match3 = self.factory.make_match(
            tournament=tournament,
            home=None,
            away=None,
            description='Match 3 - Final',
            knockout=True,
        )
        self.factory.make_prediction(
            user=user, match=match1, home_goals=1, away_goals=0
        )
        self.factory.make_prediction(
            user=user, match=match2, home_goals=0, away_goals=1
        )
        self.factory.make_prediction(
            user=user, match=match3, home_goals=2, away_goals=0
        )

        share_text = projected_bracket_share_text(tournament, user)

        self.assertLessEqual(len(share_text), 280)
        self.assertIn(
            '\n🇺🇾 \\\n     🇺🇾 \\\n🇺🇾\n          🇺🇾\n'
            '🇺🇾 \\\n     🇺🇾\n🇺🇾\n',
            share_text,
        )
        self.assertNotIn('1-0', share_text)
        self.assertNotIn('1A', share_text)

    def test_projected_bracket_advances_predicted_winners(self):
        tournament = self.factory.make_tournament(
            preferences={
                'format': {
                    'bracket': (
                        {
                            'match': 1,
                            'round': 'Round of 32',
                            'home': '1A',
                            'away': '2A',
                        },
                        {
                            'match': 2,
                            'round': 'Round of 32',
                            'home': '1B',
                            'away': '2B',
                        },
                        {
                            'match': 3,
                            'round': 'Final',
                            'home': 'W1',
                            'away': 'W2',
                        },
                    )
                }
            }
        )
        user = self.factory.make_user()
        teams = {
            slot: self.factory.make_team(name=slot, code=slot)
            for slot in ('1A', '2A', '1B', '2B')
        }
        tournament.teams.add(*teams.values())
        user.preferences['predicted_ranking'] = {
            'version': 2,
            'standings': {
                slot: team.id for slot, team in teams.items()
            },
        }
        user.save(update_fields=['preferences'])
        match1 = self.factory.make_match(
            tournament=tournament,
            home=None,
            away=None,
            description='Match 1 - Round of 32',
            knockout=True,
        )
        match2 = self.factory.make_match(
            tournament=tournament,
            home=None,
            away=None,
            description='Match 2 - Round of 32',
            knockout=True,
        )
        match3 = self.factory.make_match(
            tournament=tournament,
            home=None,
            away=None,
            description='Match 3 - Final',
            knockout=True,
        )
        self.factory.make_prediction(
            user=user, match=match1, home_goals=2, away_goals=0
        )
        self.factory.make_prediction(
            user=user, match=match2, home_goals=0, away_goals=1
        )
        self.factory.make_prediction(
            user=user, match=match3, home_goals=3, away_goals=1
        )

        bracket = projected_bracket(tournament, user)

        self.assertEqual(bracket[2]['home'], teams['1A'])
        self.assertEqual(bracket[2]['away'], teams['2B'])
        self.assertEqual(bracket[2]['winner'], teams['1A'])

    def test_projected_bracket_uses_penalties_for_tied_knockouts(self):
        tournament = self.factory.make_tournament(
            preferences={
                'format': {
                    'bracket': (
                        {
                            'match': 1,
                            'round': 'Final',
                            'home': '1A',
                            'away': '2A',
                        },
                    )
                }
            }
        )
        user = self.factory.make_user()
        home = self.factory.make_team(name='Home', code='HOM')
        away = self.factory.make_team(name='Away', code='AWY')
        tournament.teams.add(home, away)
        user.preferences['predicted_ranking'] = {
            'version': 2,
            'standings': {'1A': home.id, '2A': away.id},
        }
        user.save(update_fields=['preferences'])
        match = self.factory.make_match(
            tournament=tournament,
            home=None,
            away=None,
            description='Partido 1 - Final',
            knockout=True,
        )
        self.factory.make_prediction(
            user=user,
            match=match,
            home_goals=1,
            away_goals=1,
            penalties='V',
        )

        bracket = projected_bracket(tournament, user)

        self.assertEqual(bracket[0]['winner'], away)
        self.assertEqual(bracket[0]['loser'], home)

    def test_projected_bracket_leaves_dependents_unresolved(self):
        tournament = self.factory.make_tournament(
            preferences={
                'format': {
                    'bracket': (
                        {
                            'match': 1,
                            'round': 'Semi-final',
                            'home': '1A',
                            'away': '2A',
                        },
                        {
                            'match': 2,
                            'round': 'Final',
                            'home': 'W1',
                            'away': '1B',
                        },
                    )
                }
            }
        )
        user = self.factory.make_user()
        teams = {
            slot: self.factory.make_team(name=slot, code=slot)
            for slot in ('1A', '2A', '1B')
        }
        tournament.teams.add(*teams.values())
        user.preferences['predicted_ranking'] = {
            'version': 2,
            'standings': {
                slot: team.id for slot, team in teams.items()
            },
        }
        user.save(update_fields=['preferences'])

        bracket = projected_bracket(tournament, user)

        self.assertIsNone(bracket[0]['winner'])
        self.assertEqual(bracket[1]['home'], 'W1')
