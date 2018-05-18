# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse
from allauth.socialaccount.models import SocialApp

from ega.constants import DEFAULT_TOURNAMENT
from ega.models import EgaUser, Tournament


class BaseTestCase(TestCase):

    def setUp(self):
        super(BaseTestCase, self).setUp()
        app = SocialApp.objects.create(
            name='facebook', provider='facebook',
            client_id='lorem', secret='ipsum')
        app.sites.add(Site.objects.get_current())
        Tournament.objects.create(slug=DEFAULT_TOURNAMENT, published=True)
        Tournament.objects.create(slug='other', published=True)


class LoginTestCase(BaseTestCase):

    url = reverse('account_login')
    bad_login = (
        'El usuario y/o la contraseña que especificaste no son correctos.')

    def setUp(self):
        super(LoginTestCase, self).setUp()
        self.user = EgaUser.objects.create_user(
            username='test', password='12345678')

    def login(self, username, password, **kwargs):
        response = self.client.post(
            self.url, data=dict(login=username, password=password), **kwargs)
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
            ['Has iniciado sesión exitosamente como %s.' % self.user.username])


class SignUpTestCase(BaseTestCase):

    url = reverse('account_signup')
    bad_username = 'Ya existe un usuario con este nombre.'
    bad_email = (
        'Un usuario ya fue registrado con esta dirección de correo '
        'electrónico.')
    good_pw = '1234567U'

    def setUp(self):
        super(SignUpTestCase, self).setUp()
        self.user = EgaUser.objects.create_user(
            username='test', email='test@example.com', password=self.good_pw)

    def signup(self, username, email, password, **kwargs):
        data = {
            'username': username, 'email': email, 'password1': password,
            'password2': password, 'g-recaptcha-response': 'PASSED'}
        response = self.client.post(self.url, data=data, **kwargs)
        return response

    def test_existing_username(self):
        response = self.signup(
            self.user.username, 'foo@example.com', self.good_pw)
        self.assertFormError(response, 'form', 'username', self.bad_username)
        self.assertContains(response, self.bad_username)

    def test_existing_email(self):
        response = self.signup('zaraza', self.user.email, self.good_pw)
        self.assertFormError(response, 'form', 'email', self.bad_email)
        self.assertContains(response, self.bad_email)

    def test_success(self):
        os.environ['NORECAPTCHA_TESTING'] = 'True'
        self.addCleanup(os.environ.pop, 'NORECAPTCHA_TESTING')

        new = 'foobar'
        response = self.signup(
            new, 'foo@example.com', self.good_pw, follow=True)
        self.assertRedirects(response, reverse('meta-home'))
        self.assertEqual(
            sorted(m.message for m in response.context['messages']),
            ['Correo electrónico enviado a foo@example.com.',
             'Has iniciado sesión exitosamente como %s.' % new])
        self.assertEqual(EgaUser.objects.filter(username=new).count(), 1)
