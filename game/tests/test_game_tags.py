import datetime

from django.test import TestCase

from game.models import Tournament, MatchGroup, Match
from game.templatetags.game_tags import latest_results

class LatestResultsTestCase(TestCase):
    """Tests for latest_results template tag."""

    fixtures = ['game_data.json']

    def setUp(self):
        # setting up sample matches
        self.tournament = Tournament.objects.get(slug='torneo-de-test')
        self.another_tournament = Tournament.objects.get(slug='otro-torneo')
        
        group = MatchGroup.objects.create(tournament=self.tournament,
                                          name='Fecha 1')
        another_group = MatchGroup.objects.create(
                                            tournament=self.another_tournament,
                                            name='Fecha 1')
        team1 = self.tournament.teams.all()[0]
        team2 = self.tournament.teams.all()[1]
        match_date = datetime.datetime(2012, 2, 10, 22, 0)
        match1 = Match.objects.create(group=group, home=team1, away=team2,
                                      date=match_date, approved=True)
        match2 = Match.objects.create(group=group, home=team2, away=team1,
                                      date=match_date, approved=True)
        match3 = Match.objects.create(group=another_group, home=team2,
                                      away=team1, date=match_date,
                                      approved=True)
        match4 = Match.objects.create(group=group, home=team2, away=team1,
                                      date=match_date)


    def test_global_latest_results(self):
        """Check latest results for any tournament are returned."""
        context = latest_results()
        matches = context['matches']

        self.assertEqual(len(matches), 3)
        self.assertTrue(
            filter(lambda m: m.group.tournament==self.another_tournament,
                   matches)
        )
        self.assertTrue(
            filter(lambda m: m.group.tournament==self.tournament, matches))

    def test_specific_tournament_latest_results(self):
        """Check latest results for given tournament are returned."""
        context = latest_results(self.tournament)
        matches = context['matches']

        self.assertEqual(len(matches), 2)
        self.assertEqual(
            len(filter(lambda m: m.group.tournament==self.tournament,
                       matches)), 2)

        # only approved results
        self.assertEqual(len(filter(lambda m: not m.approved, matches)), 0)

    def test_limited_latest_results(self):
        """Check N latest results for a tournament are returned."""
        context = latest_results(latest=1)
        matches = context['matches']

        self.assertEqual(len(matches), 1)
