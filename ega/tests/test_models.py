from unittest import mock

from django.conf import settings
from django.core import mail
from django.utils.timezone import now

from ega.constants import INVITE_SUBJECT, INVITE_BODY
from ega.tests.helpers import TestCase

ADMINS = ['natalia@gmail.com', 'matias@gmail.com']


class EgaUserTestCase(TestCase):
    def test_invite_friends_no_emails(self):
        user = self.factory.make_user()
        user.invite_friends([])
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_friends(self):
        friends = ['a@a.com', 'b@b.com']
        user = self.factory.make_user()
        user.invite_friends(friends)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, INVITE_SUBJECT)
        self.assertEqual(email.body, INVITE_BODY)
        self.assertEqual(email.from_email, settings.EL_EGA_NO_REPLY)
        self.assertEqual(email.to, [settings.EL_EGA_ADMIN])
        self.assertEqual(email.bcc, friends + ADMINS)

    def test_invite_friends_custom_subject_body(self):
        friends = ['a@a.com', 'b@b.com']
        subject = 'booga booga'
        body = 'lorem ipsum sir amet.'
        user = self.factory.make_user()
        user.invite_friends(friends, subject, body)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, subject)
        self.assertEqual(email.body, body)
        self.assertEqual(email.from_email, settings.EL_EGA_NO_REPLY)
        self.assertEqual(email.to, [settings.EL_EGA_ADMIN])
        self.assertEqual(email.bcc, friends + ADMINS)

    def test_empty_preferences_default(self):
        user = self.factory.make_user()
        self.assertEqual(user.preferences, {})

    def test_default_prediction(self):
        user = self.factory.make_user()

        self.assertIsNone(user.default_prediction, None)

        right_now = now()
        with mock.patch('ega.models.now', return_value=right_now):
            user.default_prediction = (1, 0, '')

        self.assertEqual(
            user.default_prediction,
            {
                'home_goals': 1,
                'away_goals': 0,
                'penalties': '',
                'last_updated': right_now,
            },
        )
        self.assertEqual(
            user.preferences, {'default_prediction': user.default_prediction}
        )


class UpdateRelatedPredictions(TestCase):
    def finish_match(
        self,
        match,
        home_goals=0,
        away_goals=0,
        pk_home_goals=None,
        pk_away_goals=None,
    ):
        match.home_goals = home_goals
        match.away_goals = away_goals
        match.pk_home_goals = pk_home_goals
        match.pk_away_goals = pk_away_goals
        match.finished = True
        match.save()

    def assert_prediction_correct(
        self, prediction, away_goals, home_goals, penalties, score, source
    ):
        prediction.refresh_from_db()
        self.assertEqual(prediction.away_goals, away_goals)
        self.assertEqual(prediction.home_goals, home_goals)
        self.assertEqual(prediction.penalties, penalties)
        self.assertEqual(prediction.score, score)
        self.assertEqual(prediction.source, source)

    def test_updates_scores(self):
        match = self.factory.make_match()
        predictions = [
            self.factory.make_prediction(match=match) for i in range(3)
        ]

        self.finish_match(match)

        for p in predictions:
            with self.subTest(prediction=p):
                self.assert_prediction_correct(
                    p,
                    away_goals=None,
                    home_goals=None,
                    penalties='',
                    score=0,
                    source='web',
                )

    def test_update_unpredicted_prediction(self):
        default = {'home_goals': 1, 'away_goals': 0, 'penalties': ''}
        user = self.factory.make_user(
            preferences={'default_prediction': default}
        )
        assert user.default_prediction == default, user.default_prediction
        match = self.factory.make_match()
        prediction = self.factory.make_prediction(match=match, user=user)
        assert prediction.home_goals is None
        assert prediction.away_goals is None

        self.finish_match(match, 1, 0)

        self.assert_prediction_correct(
            prediction,
            home_goals=1,
            away_goals=0,
            penalties='',
            score=3,
            source='preferences',
        )

    def test_update_unpredicted_prediction_with_penalties(self):
        default = {'home_goals': 1, 'away_goals': 1, 'penalties': 'L'}
        user = self.factory.make_user(
            preferences={'default_prediction': default}
        )
        assert user.default_prediction == default, user.default_prediction
        match = self.factory.make_match()
        prediction = self.factory.make_prediction(match=match, user=user)
        assert prediction.home_goals is None
        assert prediction.away_goals is None
        assert prediction.penalties == ''

        self.finish_match(match, 1, 1)

        self.assert_prediction_correct(
            prediction,
            home_goals=1,
            away_goals=1,
            penalties='L',
            score=3,
            source='preferences',
        )

    def test_update_predicted_prediction_do_not_use_user_preferences(self):
        default = {'home_goals': 1, 'away_goals': 0}
        user = self.factory.make_user(
            preferences={'default_prediction': default}
        )
        assert user.default_prediction == default, user.default_prediction

        match = self.factory.make_match()
        prediction = self.factory.make_prediction(
            match=match, user=user, home_goals=2, away_goals=1
        )

        self.finish_match(match, 1, 0)

        self.assert_prediction_correct(
            prediction,
            home_goals=2,
            away_goals=1,
            penalties='',
            score=1,
            source='web',
        )

    def test_update_unpredicted_predictions_many(self):
        user_no_default_prediction = self.factory.make_user(
            preferences={'foo': 'bar'}
        )
        user_default_exact_result = self.factory.make_user(
            preferences={
                'default_prediction': {'home_goals': 1, 'away_goals': 2}
            }
        )
        user_default_exact_side = self.factory.make_user(
            preferences={
                'default_prediction': {'home_goals': 2, 'away_goals': 5}
            }
        )
        user_default_mismatch = self.factory.make_user(
            preferences={
                'default_prediction': {'home_goals': 1, 'away_goals': 0}
            }
        )

        match = self.factory.make_match()

        prediction_no_pref_unpredicted = self.factory.make_prediction(
            match=match
        )
        prediction_predicted_exact_result = self.factory.make_prediction(
            match=match, home_goals=1, away_goals=2
        )
        prediction_predicted_exact_side = self.factory.make_prediction(
            match=match, home_goals=0, away_goals=2
        )
        prediction_predicted_mismatch = self.factory.make_prediction(
            match=match, home_goals=1, away_goals=0
        )
        prediction_no_default_prediction = self.factory.make_prediction(
            match=match, user=user_no_default_prediction
        )

        prediction_default_exact_result = self.factory.make_prediction(
            match=match, user=user_default_exact_result
        )
        prediction_default_exact_side = self.factory.make_prediction(
            match=match, user=user_default_exact_side
        )
        prediction_default_mismatch = self.factory.make_prediction(
            match=match, user=user_default_mismatch
        )

        self.finish_match(match, 1, 2)

        self.assert_prediction_correct(
            prediction_no_pref_unpredicted,
            home_goals=None,
            away_goals=None,
            penalties='',
            score=0,
            source='web',
        )
        self.assert_prediction_correct(
            prediction_predicted_exact_result,
            home_goals=1,
            away_goals=2,
            penalties='',
            score=3,
            source='web',
        )
        self.assert_prediction_correct(
            prediction_predicted_exact_side,
            home_goals=0,
            away_goals=2,
            penalties='',
            score=1,
            source='web',
        )
        self.assert_prediction_correct(
            prediction_predicted_mismatch,
            home_goals=1,
            away_goals=0,
            penalties='',
            score=0,
            source='web',
        )
        self.assert_prediction_correct(
            prediction_no_default_prediction,
            home_goals=None,
            away_goals=None,
            penalties='',
            score=0,
            source='web',
        )

        self.assert_prediction_correct(
            prediction_default_exact_result,
            home_goals=1,
            away_goals=2,
            penalties='',
            score=3,
            source='preferences',
        )
        self.assert_prediction_correct(
            prediction_default_exact_side,
            home_goals=2,
            away_goals=5,
            penalties='',
            score=1,
            source='preferences',
        )
        self.assert_prediction_correct(
            prediction_default_mismatch,
            home_goals=1,
            away_goals=0,
            penalties='',
            score=0,
            source='preferences',
        )

    def test_update_unpredicted_prediction_many_with_penalties(self):
        user_buggy_penalties = self.factory.make_user(
            preferences={
                'default_prediction': {
                    'home_goals': 1,
                    'away_goals': 1,
                    'penalties': 'a',  # intentionally buggy
                }
            }
        )
        user_exact_score_and_penalties = self.factory.make_user(
            preferences={
                'default_prediction': {
                    'home_goals': 1,
                    'away_goals': 1,
                    'penalties': 'L',
                }
            }
        )
        user_tie_and_penalties = self.factory.make_user(
            preferences={
                'default_prediction': {
                    'home_goals': 0,
                    'away_goals': 0,
                    'penalties': 'L',
                }
            }
        )
        user_exact_score_incorrect_penalties = self.factory.make_user(
            preferences={
                'default_prediction': {
                    'home_goals': 1,
                    'away_goals': 1,
                    'penalties': 'V',
                }
            }
        )
        user_tie_incorrect_penalties = self.factory.make_user(
            preferences={
                'default_prediction': {
                    'home_goals': 0,
                    'away_goals': 0,
                    'penalties': 'V',
                }
            }
        )
        user_exact_score_empty_penalties = self.factory.make_user(
            preferences={
                'default_prediction': {
                    'home_goals': 1,
                    'away_goals': 1,
                    'penalties': '',
                }
            }
        )

        match = self.factory.make_match()

        no_default_prediction = self.factory.make_prediction(match=match)
        buggy_penalties = self.factory.make_prediction(
            match=match, user=user_buggy_penalties
        )
        exact_score_and_penalties = self.factory.make_prediction(
            match=match, user=user_exact_score_and_penalties
        )
        tie_and_penalties = self.factory.make_prediction(
            match=match, user=user_tie_and_penalties
        )
        exact_score_incorrect_penalties = self.factory.make_prediction(
            match=match, user=user_exact_score_incorrect_penalties
        )
        tie_incorrect_penalties = self.factory.make_prediction(
            match=match, user=user_tie_incorrect_penalties
        )
        exact_score_empty_penalties = self.factory.make_prediction(
            match=match, user=user_exact_score_empty_penalties
        )

        self.finish_match(match, 1, 1, 5, 4)  # tie with a 'home' penalty win

        self.assert_prediction_correct(
            no_default_prediction,
            home_goals=None,
            away_goals=None,
            penalties='',
            score=0,
            source='web',
        )
        self.assert_prediction_correct(
            buggy_penalties,
            home_goals=1,
            away_goals=1,
            penalties='',
            score=3,
            source='preferences',
        )
        self.assert_prediction_correct(
            exact_score_and_penalties,
            home_goals=1,
            away_goals=1,
            penalties='L',
            score=4,
            source='preferences',
        )
        self.assert_prediction_correct(
            tie_and_penalties,
            home_goals=0,
            away_goals=0,
            penalties='L',
            score=2,
            source='preferences',
        )
        self.assert_prediction_correct(
            exact_score_incorrect_penalties,
            home_goals=1,
            away_goals=1,
            penalties='V',
            score=3,
            source='preferences',
        )
        self.assert_prediction_correct(
            tie_incorrect_penalties,
            home_goals=0,
            away_goals=0,
            penalties='V',
            score=1,
            source='preferences',
        )
        self.assert_prediction_correct(
            exact_score_empty_penalties,
            home_goals=1,
            away_goals=1,
            penalties='',
            score=3,
            source='preferences',
        )


class PredictedRankingTestCase(TestCase):
    def test_empty(self):
        tournament = self.factory.make_tournament()
        user = self.factory.make_user()
        self.assertEqual(user.predicted_ranking(tournament), {})

    def test_update(self):
        tournament = self.factory.make_tournament()
        match1 = self.factory.make_match(tournament=tournament)
        match2 = self.factory.make_match(tournament=tournament)
        match3 = self.factory.make_match(tournament=tournament)
        user = self.factory.make_user()
        self.factory.make_prediction(
            match=match1, user=user, home_goals=1, away_goals=0
        )
        self.factory.make_prediction(
            match=match2, user=user, home_goals=2, away_goals=0
        )
        self.factory.make_prediction(
            match=match3, user=user, home_goals=3, away_goals=2
        )

        user.update_predicted_ranking(tournament)

        ranking = user.predicted_ranking(tournament)
        expected = {
            "1": match2.home.id,
            "2": match3.home.id,
            "3": match1.home.id,
            "4": match3.away.id,
            "5": match1.away.id,
            "6": match2.away.id,
        }
        self.assertEqual(ranking, expected)

    def test_update_use_zone_info(self):
        tournament = self.factory.make_tournament()
        match1 = self.factory.make_match(tournament=tournament)
        match2 = self.factory.make_match(tournament=tournament)
        for t in (match1.home, match1.away):
            t.teamstats_set.filter(tournament=tournament).update(zone="A")
        for t in (match2.home, match2.away):
            t.teamstats_set.filter(tournament=tournament).update(zone="B")

        user = self.factory.make_user()
        self.factory.make_prediction(
            match=match1, user=user, home_goals=1, away_goals=0
        )
        self.factory.make_prediction(
            match=match2, user=user, home_goals=1, away_goals=0
        )

        user.update_predicted_ranking(tournament)

        ranking = user.predicted_ranking(tournament)
        expected = {
            "1A": match1.home.id,
            "1B": match2.home.id,
            "2A": match1.away.id,
            "2B": match2.away.id,
        }
        self.assertEqual(ranking, expected)
