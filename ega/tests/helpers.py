from django.test import TestCase as BaseTestCase
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from ega.models import EgaUser, Match, Prediction, Team, Tournament


class Factory(object):
    def make_string(self, prefix='str', length=15):
        suffix = get_random_string(length - len(prefix) - 1)
        return f'{prefix}-{suffix}'

    def make_match(self, **kwargs):
        kwargs.setdefault('tournament', self.make_tournament())
        kwargs.setdefault('home', self.make_team())
        kwargs.setdefault('away', self.make_team())
        return Match.objects.create(**kwargs)

    def make_prediction(self, **kwargs):
        kwargs.setdefault('match', self.make_match())
        kwargs.setdefault('user', self.make_user())
        return Prediction.objects.create(**kwargs)

    def make_team(self, **kwargs):
        kwargs.setdefault('name', self.make_string(prefix='team'))
        kwargs.setdefault('slug', slugify(kwargs['name']))
        return Team.objects.create(**kwargs)

    def make_tournament(self, **kwargs):
        kwargs.setdefault('name', self.make_string(prefix='tournament'))
        kwargs.setdefault('slug', slugify(kwargs['name']))
        return Tournament.objects.create(**kwargs)

    def make_user(self, **kwargs):
        kwargs.setdefault('username', self.make_string(prefix='user'))
        return EgaUser.objects.create(**kwargs)


class TestCase(BaseTestCase):
    factory = Factory()
