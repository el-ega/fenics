import datetime

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase

import game_settings
from models import Tournament, MatchGroup, Match, Card, UserPosition


class GameTest(TestCase):
    """Model level testcase for game."""

    fixtures = ['game_data.json']

    def setUp(self):
        # creating test users
        self.user1 = User.objects.create_user(username='winner',
                                              email='imthewinner@fenics.com')
        self.user2 = User.objects.create_user(username='cebollita',
                                              email='secondplace@fenics.com')

        # setting up sample matches
        tournament = Tournament.objects.get(slug='torneo-de-test')
        group = MatchGroup.objects.create(tournament=tournament, name='Fecha 1')
        team1 = tournament.teams.all()[0]
        team2 = tournament.teams.all()[1]
        match_date = datetime.datetime(2012, 2, 10, 22, 0)
        self.match1 = Match.objects.create(group=group, home=team1, away=team2,
                                           date=match_date)
        self.match2 = Match.objects.create(group=group, home=team2, away=team1,
                                           date=match_date)

        # cards played for the match above
        Card.objects.create(user=self.user1, match=self.match1,
                            home_goals=2, away_goals=1)
        Card.objects.create(user=self.user2, match=self.match1,
                            home_goals=1, away_goals=0)

    def assert_card_update(self, card):
        """Check card score is correct according to related match result."""
        score = 0

        if card.home_goals == card.match.home_goals and \
           card.away_goals == card.match.away_goals:
            score = game_settings.EXACTLY_MATCH_POINTS

        elif card.home_goals > card.away_goals and \
           card.match.home_goals > card.match.away_goals:
            score = game_settings.WINNER_MATCH_POINTS

        elif card.home_goals < card.away_goals and \
           card.match.home_goals < card.match.away_goals:
            score = game_settings.WINNER_MATCH_POINTS

        elif card.home_goals == card.away_goals and \
           card.match.home_goals == card.match.away_goals:
            score = game_settings.WINNER_MATCH_POINTS

        if card.score and card.starred:
            score += game_settings.STARRED_MATCH_POINTS

        self.assertEqual(card.score, score)

    def set_match_result(self, match, home_goals, away_goals, approved=True):
        """Update match results and approval."""
        match.home_goals = home_goals
        match.away_goals = away_goals
        match.approved = approved
        match.save()

    def test_deadline(self):
        """When match date set, deadline should be HOURS_TO_DEADLINE before."""
        deadline = self.match1.deadline
        delta = datetime.timedelta(hours=game_settings.HOURS_TO_DEADLINE)
        self.assertEqual(deadline, self.match1.date - delta)

    def test_deadline_without_date(self):
        """When match date not set, deadline should return None."""
        self.match1.date = None
        self.match1.save()
        deadline = self.match1.deadline
        self.assertEqual(deadline, None)

    def test_cards_do_not_update_on_not_approved_match_save(self):
        """When saving a not approved match, related cards are not updated."""
        self.set_match_result(self.match1, 2, 1, approved=False)

        for card in self.match1.card_set.all():
            self.assertIsNone(card.score)

    def test_cards_update_on_match_save(self):
        """When saving a match, if approved, related cards should be updated."""
        self.set_match_result(self.match1, 2, 1)

        for card in self.match1.card_set.all():
            self.assert_card_update(card)

    def test_cards_update_exactly_result(self):
        """For a card with exactly result score is EXACTLY_MATCH_POINTS."""
        self.set_match_result(self.match1, 2, 1)

        expected_score = game_settings.EXACTLY_MATCH_POINTS
        card = self.user1.card_set.get(match=self.match1)
        self.assertEqual(card.score, expected_score)

        # starred case
        card.starred = True
        card.update_score()
        expected_score += game_settings.STARRED_MATCH_POINTS
        self.assertEqual(card.score, expected_score)

    def test_cards_update_winner_result(self):
        """For a card with winner coincidence score is WINNER_MATCH_POINTS."""
        self.set_match_result(self.match1, 1, 0)

        expected_score = game_settings.WINNER_MATCH_POINTS
        card = self.user1.card_set.get(match=self.match1)
        self.assertEqual(card.score, expected_score)

        # starred case
        card.starred = True
        card.update_score()
        expected_score += game_settings.STARRED_MATCH_POINTS
        self.assertEqual(card.score, expected_score)

    def test_cards_update_wrong_result(self):
        """For a card with no coincidence score is 0."""
        self.set_match_result(self.match1, 1, 1)

        card = self.user1.card_set.get(match=self.match1)
        self.assertEqual(card.score, 0)

        # starred case
        card.starred = True
        card.update_score()
        self.assertEqual(card.score, 0)
        
    def test_update_user_position(self):
        """Check user positions are updated after saving a match result."""
        self.set_match_result(self.match1, 2, 1)
        self.set_match_result(self.match2, 1, 1)

        Card.objects.create(user=self.user1, match=self.match2,
                            home_goals=0, away_goals=0)

        cards = Card.objects.all()
        score = cards.filter(user=self.user1).aggregate(total=Sum('score'))
        position1 = UserPosition.objects.get(user=self.user1)
        self.assertEqual(position1.points, score['total'])

        score = cards.filter(user=self.user2).aggregate(total=Sum('score'))
        position2 = UserPosition.objects.get(user=self.user2)
        self.assertEqual(position2.points, score['total'])
