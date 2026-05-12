from ega.bracket import build_predicted_standings, projected_bracket
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

        self.assertEqual(bracket[6]['home'], team_1a)
        self.assertEqual(bracket[6]['away'], team_3c)
