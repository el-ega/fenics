import datetime
import json

from unittest import mock

from django.contrib.sites.models import Site
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils import translation
from allauth.socialaccount.models import SocialApp

from ega.constants import DEFAULT_TOURNAMENT, ROUND16_MATCHES
from ega.models import EgaUser, Tournament
from ega.tests.helpers import TestCase


class BaseTestCase(TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        app = SocialApp.objects.create(
            name='facebook',
            provider='facebook',
            client_id='lorem',
            secret='ipsum',
        )
        app.sites.add(Site.objects.get_current())
        self.user = EgaUser.objects.create_user(
            username='user', password='password'
        )
        self.tournament = Tournament.objects.create(
            slug=DEFAULT_TOURNAMENT, published=True
        )
        Tournament.objects.create(slug='other', published=True)


class LoginTestCase(BaseTestCase):

    url = reverse('account_login')
    bad_login = (
        'El usuario y/o la contraseña que se especificaron no son correctos.'
    )

    def setUp(self):
        super(LoginTestCase, self).setUp()
        self.user = EgaUser.objects.create_user(
            username='test', password='12345678'
        )

    def login(self, username, password, **kwargs):
        response = self.client.post(
            self.url, data=dict(login=username, password=password), **kwargs
        )
        return response

    def test_non_existing_user(self):
        response = self.login('foo', 'password')
        self.assertContains(response, self.bad_login)
        self.assertFormError(response, 'form', None, self.bad_login)

    def test_bad_credentials(self):
        response = self.login(self.user.username, 'password')
        self.assertContains(response, self.bad_login)
        self.assertFormError(response, 'form', None, self.bad_login)

    def test_success(self):
        response = self.login(self.user.username, '12345678', follow=True)
        self.assertRedirects(response, reverse('meta-home'))
        self.assertEqual(
            [m.message for m in response.context['messages']],
            ['Ha iniciado sesión exitosamente como %s.' % self.user.username],
        )


class SwitchLanguageTestCase(BaseTestCase):
    def test_switch_language(self):
        url = reverse('switch-language', args=['en'])
        self.client.login(username='user', password='password')
        response = self.client.get(url, follow=True)

        self.assertRedirects(response, reverse('meta-home'))
        cur_language = translation.get_language()
        self.assertEqual(cur_language, 'en')

    def test_switch_unsupported_language(self):
        with self.assertRaises(NoReverseMatch):
            reverse('switch-language', args=['fr'])


class SignUpTestCase(BaseTestCase):

    url = reverse('account_signup')
    bad_username = 'Ya existe un usuario con este nombre.'
    bad_email = (
        'Un usuario ya ha sido registrado con esta dirección de correo '
        'electrónico.'
    )
    bad_captcha = 'Error verifying reCAPTCHA, please try again.'
    good_pw = 'Pl3aseLe7Me1n'

    def setUp(self):
        super(SignUpTestCase, self).setUp()
        self.user = EgaUser.objects.create_user(
            username='test', email='test@example.com', password=self.good_pw
        )

    def signup(
        self,
        username,
        email,
        password,
        captcha_valid=True,
        captcha_score=0.91,
        **kwargs
    ):
        data = {
            'username': username,
            'email': email,
            'password1': password,
            'password2': password,
            'captcha': 'test',
        }
        check_captcha = mock.Mock(
            is_valid=captcha_valid, extra_data={'score': captcha_score}
        )
        with mock.patch('captcha.client.submit', return_value=check_captcha):
            response = self.client.post(
                self.url, data=data, follow=True, **kwargs
            )
        return response

    def test_existing_username(self):
        response = self.signup(
            self.user.username, 'foo@example.com', self.good_pw
        )
        self.assertFormError(response, 'form', 'username', self.bad_username)
        self.assertContains(response, self.bad_username)

    def test_existing_email(self):
        response = self.signup('zaraza', self.user.email, self.good_pw)
        self.assertFormError(response, 'form', 'email', self.bad_email)
        self.assertContains(response, self.bad_email)

    def test_success(self):
        new = 'foobar'
        response = self.signup(new, 'foo@example.com', self.good_pw)
        self.assertRedirects(response, reverse('meta-home'))
        self.assertEqual(
            sorted(m.message for m in response.context['messages']),
            [
                'Correo electrónico enviado a foo@example.com.',
                'Ha iniciado sesión exitosamente como %s.' % new,
            ],
        )
        self.assertEqual(EgaUser.objects.filter(username=new).count(), 1)

    def test_invalid_captcha(self):
        response = self.signup(
            'foo', 'foo@example.com', self.good_pw, captcha_valid=False
        )

        self.assertFormError(response, 'form', 'captcha', self.bad_captcha)
        self.assertContains(response, self.bad_captcha)

    def test_low_score_captcha(self):
        response = self.signup(
            'foo',
            'foo@example.com',
            self.good_pw,
            captcha_valid=True,
            captcha_score=0.89,
        )

        self.assertFormError(response, 'form', 'captcha', self.bad_captcha)
        self.assertContains(response, self.bad_captcha)


class NextMatchesTestCase(BaseTestCase):
    def test_save_updates_predicted_ranking(self):
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        m = self.factory.make_match(tournament=self.tournament, when=tomorrow)
        p = self.factory.make_prediction(match=m, user=self.user)
        assert self.user.predicted_ranking(self.tournament) == {}

        url = reverse("ega-next-matches", kwargs={"slug": DEFAULT_TOURNAMENT})
        headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        data = {
            'form-INITIAL_FORMS': '1',
            'form-TOTAL_FORMS': '1',
            "form-MAX_NUM_FORMS": "1",
            "form-0-home_goals": 1,
            "form-0-away_goals": 0,
            "form-0-id": p.id,
        }
        self.client.login(username='user', password='password')
        response = self.client.post(url, data=data, **headers)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["ok"])

        self.user.refresh_from_db()
        ranking = self.user.predicted_ranking(self.tournament)
        self.assertEqual(ranking, {"1": m.home.id, "2": m.away.id})


class HomeTestCase(BaseTestCase):
    def test_round16_default(self):
        self.client.login(username='user', password='password')

        url = reverse("ega-home", kwargs={"slug": DEFAULT_TOURNAMENT})
        response = self.client.get(url)

        self.assertEqual(tuple(response.context["round16"]), ROUND16_MATCHES)

    def test_round16_prediction_based(self):
        match1 = self.factory.make_match(tournament=self.tournament)
        match2 = self.factory.make_match(tournament=self.tournament)
        for t in (match1.home, match1.away):
            t.teamstats_set.filter(tournament=self.tournament).update(zone="A")
            self.tournament.teams.add(t)
        for t in (match2.home, match2.away):
            t.teamstats_set.filter(tournament=self.tournament).update(zone="B")
            self.tournament.teams.add(t)
        self.factory.make_prediction(
            user=self.user, match=match1, home_goals=1, away_goals=0
        )
        self.factory.make_prediction(
            user=self.user, match=match2, home_goals=1, away_goals=0
        )
        self.user.update_predicted_ranking(self.tournament)
        self.client.login(username='user', password='password')

        url = reverse("ega-home", kwargs={"slug": DEFAULT_TOURNAMENT})
        response = self.client.get(url)

        ranking = {
            "1A": match1.home,
            "2A": match1.away,
            "1B": match2.home,
            "2B": match2.away,
        }
        expected = [
            (ranking.get(home, home), ranking.get(away, away))
            for home, away in ROUND16_MATCHES
        ]
        self.assertEqual(response.context["round16"], expected)
