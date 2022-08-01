from __future__ import unicode_literals

from django.conf import settings
from django.core import mail

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
        user.default_prediction = (1, 0)

        self.assertEqual(
            user.default_prediction, {'home_goals': 1, 'away_goals': 0}
        )
        self.assertEqual(
            user.preferences, {'default_prediction': user.default_prediction}
        )


class UpdateRelatedPredictions(TestCase):
    def finish_match(self, match, home_goals=0, away_goals=0):
        match.home_goals = home_goals
        match.away_goals = away_goals
        match.finished = True
        match.save()

    def assert_prediction_correct(
        self, prediction, away_goals, home_goals, score, source
    ):
        prediction.refresh_from_db()
        self.assertEqual(prediction.away_goals, away_goals)
        self.assertEqual(prediction.home_goals, home_goals)
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
                    p, away_goals=None, home_goals=None, score=0, source='web'
                )

    def test_update_unpredicted_prediction(self):
        default = {'home_goals': 1, 'away_goals': 0}
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
            prediction, home_goals=2, away_goals=1, score=1, source='web'
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
            score=0,
            source='web',
        )
        self.assert_prediction_correct(
            prediction_predicted_exact_result,
            home_goals=1,
            away_goals=2,
            score=3,
            source='web',
        )
        self.assert_prediction_correct(
            prediction_predicted_exact_side,
            home_goals=0,
            away_goals=2,
            score=1,
            source='web',
        )
        self.assert_prediction_correct(
            prediction_predicted_mismatch,
            home_goals=1,
            away_goals=0,
            score=0,
            source='web',
        )
        self.assert_prediction_correct(
            prediction_no_default_prediction,
            home_goals=None,
            away_goals=None,
            score=0,
            source='web',
        )

        self.assert_prediction_correct(
            prediction_default_exact_result,
            home_goals=1,
            away_goals=2,
            score=3,
            source='preferences',
        )
        self.assert_prediction_correct(
            prediction_default_exact_side,
            home_goals=2,
            away_goals=5,
            score=1,
            source='preferences',
        )
        self.assert_prediction_correct(
            prediction_default_mismatch,
            home_goals=1,
            away_goals=0,
            score=0,
            source='preferences',
        )
