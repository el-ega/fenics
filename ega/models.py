# -*- coding: utf-8 -*-

import random
import string

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail.message import EmailMessage
from django.db import IntegrityError, connection, models
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.timezone import now

from ega.constants import (
    DEFAULT_TOURNAMENT,
    EXACTLY_MATCH_POINTS,
    HOURS_TO_DEADLINE,
    INVITE_BODY,
    INVITE_SUBJECT,
    MATCH_WON_POINTS,
    MATCH_TIE_POINTS,
    MATCH_LOST_POINTS,
    NEXT_MATCHES_DAYS,
    WINNER_MATCH_POINTS,
)
from ega.managers import LeagueManager, PredictionManager


ALNUM_CHARS = string.ascii_letters + string.digits
RANKING_SQL = """
SELECT u.username as username, u.avatar as avatar,
       r.x1 as x1, r.x3 as x3, r.xx1 as xx1, r.xx3 as xx3, r.total as total
FROM (SELECT
    pred.user_id,
    SUM(case when score=1 then 1 else 0 end) AS x1,
    SUM(case when score=3 then 1 else 0 end) AS x3,
    SUM(case when score=2 then 1 else 0 end) AS xx1,
    SUM(case when score=4 then 1 else 0 end) AS xx3, SUM(score) AS total
    FROM ega_prediction pred
    INNER JOIN ega_match m ON (pred.match_id=m.id) {where}
    GROUP BY pred.user_id
) r INNER JOIN ega_egauser u ON (r.user_id=u.id) ORDER BY total DESC, x3 DESC
"""


def rand_str(length=20):
    return ''.join(random.choice(ALNUM_CHARS) for x in range(length))


def dictfetchall(cursor):
    """Returns all rows from a cursor as a dict."""
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


class EgaUser(AbstractUser):

    avatar = models.ImageField(
        upload_to='avatars', null=True, blank=True,
        help_text='Se recomienda subir una imagen de (al menos) 100x100')
    invite_key = models.CharField(
        max_length=20, unique=True, default=rand_str)

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
        tz_now = now() + timedelta(hours=HOURS_TO_DEADLINE)
        predictions = Prediction.objects.filter(
            match__tournament=tournament, user=self, match__when__lte=tz_now)
        predictions = predictions.order_by('-match__when')
        return predictions

    def stats(self, tournament, round=None):
        """User stats for given tournament."""
        stats = {}
        ranking = Prediction.objects.filter(
            match__tournament=tournament, user=self, score__gte=0,
            home_goals__isnull=False, away_goals__isnull=False)
        if round is not None:
            ranking = ranking.filter(match__round=round)

        stats['count'] = len(ranking)
        stats['score'] = sum(r.score for r in ranking)
        stats['winners'] = sum(1 for r in ranking if r.score > 0)
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

    def current_round(self):
        current = None
        try:
            last_played = self.match_set.filter(
                home_goals__isnull=False,
                away_goals__isnull=False).latest('when')
            current = last_played.round
        except Match.DoesNotExist:
            pass
        return current

    def next_matches(self, days=NEXT_MATCHES_DAYS):
        """Return matches in the next days."""
        tz_now = now() + timedelta(hours=HOURS_TO_DEADLINE)
        until = tz_now + timedelta(days=days)
        return self.match_set.filter(when__range=(tz_now, until))

    def ranking(self, round=None):
        """Users ranking in the tournament."""
        params = [self.id]
        where = "WHERE m.tournament_id = %s "
        if round is not None:
            where += "AND m.round = %s "
            params += [round]

        sql = RANKING_SQL.format(where=where)
        cursor = connection.cursor()
        cursor.execute(sql, params)
        ranking = dictfetchall(cursor)
        return ranking


class Team(models.Model):
    """Team metadata."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=8, blank=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='teams', null=True, blank=True)

    def __unicode__(self):
        return self.name

    def latest_matches(self, tournament=DEFAULT_TOURNAMENT):
        """Return team previously played matches."""
        tz_now = now()
        matches = Match.objects.filter(
            Q(away=self) | Q(home=self),
            tournament__slug=tournament,
            when__lte=tz_now)
        matches = matches.order_by('-when')
        return matches


class Match(models.Model):
    """Match metadata."""
    home = models.ForeignKey(Team, related_name='home_games')
    away = models.ForeignKey(Team, related_name='away_games')
    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)

    tournament = models.ForeignKey('Tournament')
    round = models.CharField(max_length=128, blank=True)
    description = models.CharField(max_length=128, blank=True)
    when = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    referee = models.CharField(max_length=200, blank=True)
    starred = models.BooleanField(default=False)
    suspended = models.BooleanField(default=False)

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

    @property
    def is_expired(self):
        return self.deadline < now()


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

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    tournament = models.ForeignKey(Tournament)
    created = models.DateTimeField(default=now)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='LeagueMember')

    objects = LeagueManager()

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'tournament'), ('slug', 'tournament'))

    def __unicode__(self):
        return self.name

    @property
    def owner(self):
        return LeagueMember.objects.get(league=self, is_owner=True).user

    def ranking(self, round=None):
        ranking = self.tournament.ranking(round=round)
        users = self.members.values_list('username', flat=True)
        ranking = [r for r in ranking if r['username'] in users]
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
    date_joined = models.DateTimeField(default=now)

    class Meta:
        unique_together = ('user', 'league')

    def __unicode__(self):
        return unicode(self.user)


@receiver(post_save, sender=Match, dispatch_uid="update-scores")
def update_related_predictions(sender, instance, **kwargs):
    """Update score for predictions related to the changed match."""
    home_goals = instance.home_goals
    away_goals = instance.away_goals
    predictions = instance.prediction_set

    if home_goals is None or away_goals is None:
        # update starred field for predictions (only while not played)
        predictions.update(starred=instance.starred)
        return

    # reset predictions
    predictions.update(score=0)

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
