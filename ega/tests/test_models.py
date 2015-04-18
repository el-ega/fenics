from django.conf import settings
from django.core import mail
from django.test import TestCase

from ega.models import EgaUser
from ega.constants import INVITE_SUBJECT, INVITE_BODY

ADMINS = ['natalia@gmail.com', 'matias@gmail.com']


class EgaUserTestCase(TestCase):

    def setUp(self):
        super(EgaUserTestCase, self).setUp()
        self.user = EgaUser.objects.create()

    def test_invite_friends_no_emails(self):
        self.user.invite_friends([])
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_friends(self):
        friends = ['a@a.com', 'b@b.com']
        self.user.invite_friends(friends)

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
        self.user.invite_friends(friends, subject, body)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, subject)
        self.assertEqual(email.body, body)
        self.assertEqual(email.from_email, settings.EL_EGA_NO_REPLY)
        self.assertEqual(email.to, [settings.EL_EGA_ADMIN])
        self.assertEqual(email.bcc, friends + ADMINS)
