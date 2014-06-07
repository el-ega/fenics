# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import random
import string

from datetime import datetime, timedelta
from functools import partial

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail.message import EmailMessage
from django.db import IntegrityError, models
from django.db.models import Count, F, Q, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from ega.constants import (
    EXACTLY_MATCH_POINTS,
    HOURS_TO_DEADLINE,
    INVITE_BODY,
    INVITE_SUBJECT,
    LEAGUE_JOIN_CHOICES,
    MATCH_WON_POINTS,
    MATCH_TIE_POINTS,
    MATCH_LOST_POINTS,
    NEXT_MATCHES_DAYS,
    WINNER_MATCH_POINTS,
)
from ega.managers import PredictionManager


ALNUM_CHARS = string.letters + string.digits


def rand_str(length=8):
    return ''.join(random.choice(ALNUM_CHARS) for x in xrange(length))


class EgaUser(AbstractUser):

    avatar = models.ImageField(
        upload_to='avatars', null=True, blank=True,
        help_text='Se recomienda subir una imagen de (al menos) 100x100')
    invite_key = models.CharField(
        max_length=20, default=partial(rand_str, 20), unique=True)

    def invite_friends(self, emails, subject=None, body=None):
        if subject is None:
            subject = INVITE_SUBJECT
        if body is None:
            body = INVITE_BODY
        if emails:
            EmailMessage(
                subject, body, from_email=settings.EL_EGA_NO_REPLY,
                to=[settings.EL_EGA_ADMIN],
                bcc=emails + [e for _, e in settings.ADMINS],
                headers={'Reply-To': self.email}).send()
        return len(emails)

    def visible_name(self):
        result = self.get_full_name()
        if not result:
            result = self.username
        return result

    def history(self, tournament):
        """Return matches predictions for given tournament."""
        now = datetime.utcnow()
        predictions = Prediction.objects.filter(
            match__tournament=tournament, user=self, match__when__lte=now,
            match__home_goals__isnull=False, match__away_goals__isnull=False)
        return predictions

    def stats(self, tournament):
        """User stats for given tournament."""
        stats = {}
        ranking = Prediction.objects.filter(
            match__tournament=tournament, user=self, score__gte=0)
        stats['count'] = len(ranking)
        stats['score'] = sum(r.score for r in ranking)
        stats['winners'] = sum(r.score for r in ranking if r.score > 0)
        stats['exacts'] = sum(1 for r in ranking
                              if r.score == EXACTLY_MATCH_POINTS)
        return stats


class Tournament(models.Model):
    """Tournament metadata."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    teams = models.ManyToManyField('Team')
    published = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def next_matches(self, days=NEXT_MATCHES_DAYS):
        """Return matches in the next days."""
        now = datetime.utcnow()
        until = now + timedelta(days=days)
        return self.match_set.filter(when__range=(now, until))

    def ranking(self):
        """Users ranking in the tournament."""
        ranking = Prediction.objects.filter(
            match__tournament=self).values('user__username').annotate(
                total=Sum('score'), count=Count('id')).order_by('-total')
        return ranking


class Team(models.Model):
    """Team metadata."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='teams', null=True, blank=True)

    def __unicode__(self):
        return self.name

    def latest_matches(self, tournament=None):
        """Return team previously played matches."""
        now = datetime.now()
        matches = Match.objects.filter(
            Q(away=self)|Q(home=self), when__lte=now)
        return matches


class Match(models.Model):
    """Match metadata."""
    home = models.ForeignKey(Team, related_name='home_games')
    away = models.ForeignKey(Team, related_name='away_games')
    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)

    tournament = models.ForeignKey('Tournament')
    when = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    referee = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ('when',)

    def __unicode__(self):
        return u"%s: %s vs %s" % (
            self.tournament, self.home.name, self.away.name)

    @property
    def deadline(self):
        """Return deadline datetime or None if match date is not set."""
        ret = None
        if self.when:
            ret = self.when - timedelta(hours=HOURS_TO_DEADLINE)
        return ret


class Prediction(models.Model):
    """User prediction for a match."""
    TRENDS = ('L', 'E', 'V')

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    match = models.ForeignKey('Match')

    home_goals = models.PositiveIntegerField(null=True, blank=True)
    away_goals = models.PositiveIntegerField(null=True, blank=True)
    trend = models.CharField(max_length=1, editable=False)
    starred = models.BooleanField(default=False)

    score = models.PositiveIntegerField(default=0)

    objects = PredictionManager()

    class Meta:
        ordering = ('match__when',)
        unique_together = ('user', 'match')

    def __unicode__(self):
        return u"%s: %s" % (self.user, self.match)

    @property
    def home_team_stats(self):
        stats, _ = self.match.home.teamstats_set.get_or_create(
            tournament=self.match.tournament)
        return stats

    @property
    def away_team_stats(self):
        stats, _ = self.match.away.teamstats_set.get_or_create(
            tournament=self.match.tournament)
        return stats

    def save(self, *args, **kwargs):
        # set trend value before saving
        if self.home_goals is not None and self.away_goals is not None:
            if self.home_goals > self.away_goals:
                self.trend = self.TRENDS[0]
            elif self.home_goals < self.away_goals:
                self.trend = self.TRENDS[2]
            else:
                self.trend = self.TRENDS[1]
        super(Prediction, self).save(*args, **kwargs)


class TeamStats(models.Model):
    """Stats for a team in a given tournament."""

    team = models.ForeignKey(Team)
    tournament = models.ForeignKey(Tournament)

    won = models.PositiveIntegerField(default=0)
    tie = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)

    points = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('-points',)

    def __unicode__(self):
        return u"%s - %s" % (self.team, self.tournament)

    def sync(self):
        """Update team stats for tournament."""
        home = Match.objects.filter(
            tournament=self.tournament, home=self.team,
            home_goals__isnull=False, away_goals__isnull=False)
        away = Match.objects.filter(
            tournament=self.tournament, away=self.team,
            home_goals__isnull=False, away_goals__isnull=False)

        self.won = (
            home.filter(home_goals__gt=F('away_goals')).count() +
            away.filter(away_goals__gt=F('home_goals')).count())
        self.tie = (
            home.filter(home_goals=F('away_goals')).count() +
            away.filter(away_goals=F('home_goals')).count())
        self.lost = (
            home.filter(home_goals__lt=F('away_goals')).count() +
            away.filter(away_goals__lt=F('home_goals')).count())

        self.points = self._points()
        self.save()

    def _points(self):
        return (self.won * MATCH_WON_POINTS +
                self.tie * MATCH_TIE_POINTS +
                self.lost * MATCH_LOST_POINTS)


class League(models.Model):
    """Custom league metadata."""

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    tournament = models.ForeignKey(Tournament)
    created = models.DateTimeField(default=datetime.utcnow)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='LeagueMember')

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @property
    def owner(self):
        return LeagueMember.objects.get(league=self, is_owner=True).user

    def ranking(self):
        ranking = self.tournament.ranking().filter(user__in=self.members.all())
        return ranking

    def save(self, *args, **kwargs):
        # generate slug
        counter = 0
        self.slug = slug = slugify(self.name)
        while True:
            try:
                result = super(League, self).save(*args, **kwargs)
            except IntegrityError:
                counter += 1
                self.slug = '%s-%s' % (slug, counter)
            else:
                break
        return result


class LeagueMember(models.Model):
    """A league member."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    league = models.ForeignKey(League)
    is_owner = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=datetime.utcnow)

    class Meta:
        unique_together = ('user', 'league')


@receiver(post_save, sender=Match, dispatch_uid="update-scores")
def update_related_predictions(sender, instance, **kwargs):
    """Update score for predictions related to the changed match."""
    home_goals = instance.home_goals
    away_goals = instance.away_goals
    predictions = instance.prediction_set

    # update exact predictions
    predictions.filter(home_goals=home_goals, away_goals=away_goals).update(
        score=EXACTLY_MATCH_POINTS)

    # update winner predictions
    if home_goals > away_goals:
        predictions.exclude(
            home_goals=home_goals, away_goals=away_goals).filter(
                home_goals__gt=F('away_goals')).update(
                    score=WINNER_MATCH_POINTS)
    elif home_goals < away_goals:
        predictions.exclude(
            home_goals=home_goals, away_goals=away_goals).filter(
                home_goals__lt=F('away_goals')).update(
                    score=WINNER_MATCH_POINTS)
    else:
        predictions.exclude(
            home_goals=home_goals, away_goals=away_goals).filter(
                home_goals=F('away_goals'), home_goals__isnull=False).update(
                    score=WINNER_MATCH_POINTS)

    # update starred predictions
    predictions.filter(score__gt=0, starred=True).update(score=F('score') + 1)


@receiver(post_save, sender=Match, dispatch_uid="update-stats")
def update_related_stats(sender, instance, **kwargs):
    """Update team stats related to the changed match."""
    for team in (instance.home, instance.away):
        stats, created = TeamStats.objects.get_or_create(
            team=team, tournament=instance.tournament)
        stats.sync()
