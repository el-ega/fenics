import collections
import json
import random
import string

from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail.message import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, connection, models
from django.db.models import Case, F, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.functions import Cast
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.timezone import now

from ega.constants import (
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
from ega.managers import LeagueManager, PredictionManager, TeamStatsManager


ALNUM_CHARS = string.ascii_letters + string.digits
RANKING_SQL = """
SELECT u.username as username, u.avatar as avatar,
       r.x1 as x1, r.x3 as x3, r.xx1 as xx1, r.xx3 as xx3,
       cp.score as champion, cp.score + r.total as total
FROM (SELECT
    pred.user_id,
    SUM(case when score=1 then 1 else 0 end) AS x1,
    SUM(case when score=3 then 1 else 0 end) AS x3,
    SUM(case when score=2 then 1 else 0 end) AS xx1,
    SUM(case when score=4 then 1 else 0 end) AS xx3,
    SUM(score) AS total
    FROM ega_prediction pred
    INNER JOIN ega_match m ON (pred.match_id=m.id)
    WHERE tournament_id=%s
    GROUP BY pred.user_id
) r
INNER JOIN ega_championprediction cp
    ON (cp.user_id=r.user_id AND cp.tournament_id=%s)
INNER JOIN ega_egauser u ON (r.user_id=u.id)
ORDER BY total DESC, x3 DESC, champion DESC
"""
ROUND_RANKING_SQL = """
SELECT u.username as username, u.avatar as avatar,
       r.x1 as x1, r.x3 as x3, r.xx1 as xx1, r.xx3 as xx3,
       r.total as total
FROM (SELECT
    pred.user_id,
    SUM(case when score=1 then 1 else 0 end) AS x1,
    SUM(case when score=3 then 1 else 0 end) AS x3,
    SUM(case when score=2 then 1 else 0 end) AS xx1,
    SUM(case when score=4 then 1 else 0 end) AS xx3,
    SUM(score) AS total
    FROM ega_prediction pred
    INNER JOIN ega_match m ON (pred.match_id=m.id)
    WHERE tournament_id=%s AND m.round=%s
    GROUP BY pred.user_id
) r
INNER JOIN ega_egauser u ON (r.user_id=u.id)
ORDER BY total DESC, x3 DESC
"""


def rand_str(length=20):
    return ''.join(random.choice(ALNUM_CHARS) for x in range(length))


def dictfetchall(cursor):
    """Returns all rows from a cursor as a dict."""
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()
    ]


class EgaUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='avatars',
        null=True,
        blank=True,
        help_text='Se recomienda subir una imagen de (al menos) 100x100',
    )
    invite_key = models.CharField(max_length=20, unique=True, default=rand_str)
    referred_by = models.ForeignKey(
        'self', null=True, related_name='referrals', on_delete=models.CASCADE
    )
    referred_on = models.DateTimeField(null=True)
    preferences = models.JSONField(encoder=DjangoJSONEncoder, default=dict)

    @property
    def default_prediction(self):
        return self.preferences.get('default_prediction')

    @default_prediction.setter
    def default_prediction(self, prediction):
        if prediction is None:
            self.preferences.pop('default_prediction', None)
        else:
            (home_goals, away_goals, penalties) = prediction
            self.preferences['default_prediction'] = {
                'home_goals': home_goals,
                'away_goals': away_goals,
                'penalties': penalties,
                'last_updated': now(),
            }

    def predicted_ranking(self, tournament):
        return self.preferences.get('predicted_ranking', {})

    def update_predicted_ranking(self, tournament):
        preds = self.prediction_set.filter(
            match__tournament=tournament,
            match__knockout=False,
            home_goals__isnull=False,
            away_goals__isnull=False,
        )

        # track (points, goal diff, goals) per team
        stats = defaultdict(lambda: (0, 0, 0))
        for p in preds:
            home_points = away_points = MATCH_TIE_POINTS
            if p.home_goals > p.away_goals:
                home_points = MATCH_WON_POINTS
                away_points = MATCH_LOST_POINTS
            elif p.home_goals < p.away_goals:
                home_points = MATCH_LOST_POINTS
                away_points = MATCH_WON_POINTS
            home_update = (
                home_points,
                p.home_goals - p.away_goals,
                p.home_goals,
            )
            away_update = (
                away_points,
                p.away_goals - p.home_goals,
                p.away_goals,
            )
            stats[p.match.home_id] = tuple(
                map(sum, zip(stats[p.match.home_id], home_update))
            )
            stats[p.match.away_id] = tuple(
                map(sum, zip(stats[p.match.away_id], away_update))
            )

        standings = sorted(stats.items(), key=lambda i: i[1], reverse=True)
        stats = TeamStats.objects.filter(tournament=tournament)
        zones = {s.team_id: s.zone for s in stats}
        counters = defaultdict(lambda: 1)
        rankings = {}
        for team_id, _ in standings:
            zone = zones[team_id]
            pos = counters[zone]
            counters[zone] += 1
            label = '{}{}'.format(pos, zone)
            rankings[label] = team_id
        self.preferences['predicted_ranking'] = rankings
        self.save(update_fields=['preferences'])

    def record_referral(self, other):
        created = False
        if other.referred_by is None:
            other.referred_by = self
            other.referred_on = now()
            other.save(update_fields=('referred_by', 'referred_on'))
            created = True
        return created

    def invite_friends(self, emails, subject=None, body=None):
        if subject is None:
            subject = INVITE_SUBJECT
        if body is None:
            body = INVITE_BODY
        if emails:
            EmailMessage(
                subject,
                body,
                from_email=settings.EL_EGA_NO_REPLY,
                to=[settings.EL_EGA_ADMIN],
                bcc=emails + [e for _, e in settings.ADMINS],
                headers={'Reply-To': self.email},
            ).send()
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
            match__tournament=tournament, user=self, match__when__lte=tz_now
        )
        predictions = predictions.order_by('-match__when')
        return predictions

    def stats(self, tournament, round=None):
        """User stats for given tournament."""
        stats = {}
        ranking = Prediction.objects.filter(
            match__tournament=tournament,
            user=self,
            score__gte=0,
            match__finished=True,
        )
        if round is not None:
            ranking = ranking.filter(match__round=round)

        stats['count'] = len(ranking)
        stats['score'] = sum(r.score for r in ranking)
        stats['winners'] = sum(1 for r in ranking if r.score > 0)
        stats['exacts'] = sum(
            1 for r in ranking if r.score == EXACTLY_MATCH_POINTS
        )
        return stats


class Tournament(models.Model):
    """Tournament metadata."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    teams = models.ManyToManyField('Team')
    image = models.ImageField(upload_to='tournaments', null=True, blank=True)
    published = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def current_round(self):
        current = None
        try:
            last_played = self.match_set.filter(finished=True).latest('when')
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
        if round is not None:
            params = [self.id, round]
            query = ROUND_RANKING_SQL
        else:
            params = [self.id, self.id]
            query = RANKING_SQL

        cursor = connection.cursor()
        cursor.execute(query, params)
        ranking = dictfetchall(cursor)
        return ranking

    def team_ranking(self):
        """Return tournament teams ranking."""
        ranking = (
            self.teamstats_set.all()
            .annotate(
                played=F('won') + F('tie') + F('lost'), dg=F('gf') - F('gc')
            )
            .order_by('zone', '-points', '-dg', '-gf', 'tie_breaker')
        )
        return ranking

    def most_common_results(self, n):
        """Return the most common results."""
        results = self.match_set.filter(
            home_goals__isnull=False, away_goals__isnull=False
        )
        results = results.values_list('home_goals', 'away_goals')
        counter = collections.Counter(results)
        return counter.most_common(n)

    def most_common_predictions(self, n):
        """Return the most common predictions."""
        predictions = Prediction.objects.filter(match__tournament=self)
        predictions = predictions.filter(
            match__home_goals__isnull=False,
            match__away_goals__isnull=False,
            home_goals__isnull=False,
            away_goals__isnull=False,
        )
        predictions = predictions.values_list('home_goals', 'away_goals')
        counter = collections.Counter(predictions)
        return counter.most_common(n)


class Team(models.Model):
    """Team metadata."""

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=8, blank=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='teams', null=True, blank=True)
    emoji = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return self.name

    def latest_matches(self, tournament):
        """Return team previously played matches."""
        tz_now = now()
        matches = Match.objects.filter(
            Q(away=self) | Q(home=self),
            tournament=tournament,
            finished=True,
            when__lte=tz_now,
        )
        matches = matches.order_by('-when')
        return matches


class Match(models.Model):
    """Match metadata."""

    home = models.ForeignKey(
        Team,
        blank=True,
        null=True,
        related_name='home_games',
        on_delete=models.CASCADE,
    )
    home_placeholder = models.CharField(max_length=200, blank=True)
    away = models.ForeignKey(
        Team,
        blank=True,
        null=True,
        related_name='away_games',
        on_delete=models.CASCADE,
    )
    away_placeholder = models.CharField(max_length=200, blank=True)
    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)
    pk_home_goals = models.IntegerField(null=True, blank=True)
    pk_away_goals = models.IntegerField(null=True, blank=True)

    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE)
    round = models.CharField(max_length=128, blank=True)
    knockout = models.BooleanField(default=False)

    description = models.CharField(max_length=128, blank=True)
    when = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    referee = models.CharField(max_length=200, blank=True)

    starred = models.BooleanField(default=False)
    suspended = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    class Meta:
        ordering = ('when',)

    def __str__(self):
        home = self.home.name if self.home else self.home_placeholder
        away = self.away.name if self.away else self.away_placeholder
        return "%s vs %s" % (home, away)

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

    SOURCES = ('preferences', 'web')
    TRENDS = ('L', 'E', 'V')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    last_updated = models.DateTimeField(auto_now=True, null=True)
    match = models.ForeignKey('Match', on_delete=models.CASCADE)

    home_goals = models.PositiveIntegerField(null=True, blank=True)
    away_goals = models.PositiveIntegerField(null=True, blank=True)
    # only knockout, and for ties
    penalties = models.CharField(max_length=1, blank=True)

    trend = models.CharField(max_length=1, editable=False)
    starred = models.BooleanField(default=False)

    score = models.PositiveIntegerField(default=0)
    source = models.CharField(
        max_length=256, default='web', choices=((s, s) for s in SOURCES)
    )

    objects = PredictionManager()

    class Meta:
        ordering = ('match__when',)
        unique_together = ('user', 'match')

    def __str__(self):
        return "%s: %s" % (self.user, self.match)

    @property
    def home_team_stats(self):
        if self.match.home is None:
            return None
        stats, _ = self.match.home.teamstats_set.get_or_create(
            tournament=self.match.tournament
        )
        return stats

    @property
    def away_team_stats(self):
        if self.match.away is None:
            return None
        stats, _ = self.match.away.teamstats_set.get_or_create(
            tournament=self.match.tournament
        )
        return stats

    @property
    def penalties_home(self):
        return self.penalties == 'L'

    @property
    def penalties_away(self):
        return self.penalties == 'V'

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


class ChampionPrediction(models.Model):
    """User prediction for tournament champion."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE)
    team = models.ForeignKey(
        'Team', blank=True, null=True, on_delete=models.CASCADE
    )
    score = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    log = models.TextField(blank=True)

    class Meta:
        unique_together = (('user', 'tournament'),)

    def __str__(self):
        return "%s - %s" % (self.user.username, self.team)

    def save(self, *args, **kwargs):
        # update log before saving
        if self.last_updated:
            log = json.loads(self.log) if self.log else []
            log.append(
                dict(
                    timestamp=self.last_updated.isoformat(),
                    team=self.team.name if self.team else None,
                )
            )
            self.log = json.dumps(log)
        super(ChampionPrediction, self).save(*args, **kwargs)


class TeamStats(models.Model):
    """Stats for a team in a given tournament."""

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)

    zone = models.CharField(default='', max_length=64, blank=True)

    won = models.PositiveIntegerField(default=0)
    tie = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)

    gf = models.PositiveIntegerField(default=0)
    gc = models.PositiveIntegerField(default=0)

    points = models.PositiveIntegerField(default=0)
    tie_breaker = models.PositiveIntegerField(default=0)

    objects = TeamStatsManager()

    class Meta:
        ordering = ('-points',)
        unique_together = (('tournament', 'team'),)

    def __str__(self):
        return "%s - %s" % (self.team, self.tournament)

    def sync(self):
        """Update team stats for tournament."""
        home = Match.objects.filter(
            tournament=self.tournament,
            home=self.team,
            knockout=False,
            finished=True,
        )
        away = Match.objects.filter(
            tournament=self.tournament,
            away=self.team,
            knockout=False,
            finished=True,
        )

        self.won = (
            home.filter(home_goals__gt=F('away_goals')).count()
            + away.filter(away_goals__gt=F('home_goals')).count()
        )
        self.tie = (
            home.filter(home_goals=F('away_goals')).count()
            + away.filter(away_goals=F('home_goals')).count()
        )
        self.lost = (
            home.filter(home_goals__lt=F('away_goals')).count()
            + away.filter(away_goals__lt=F('home_goals')).count()
        )

        # goals stats
        home_goals = home.aggregate(
            home_gf=Sum('home_goals'), home_gc=Sum('away_goals')
        )
        away_goals = away.aggregate(
            away_gf=Sum('away_goals'), away_gc=Sum('home_goals')
        )
        self.gf = 0
        if home_goals['home_gf'] is not None:
            self.gf += home_goals['home_gf']
        if away_goals['away_gf'] is not None:
            self.gf += away_goals['away_gf']

        self.gc = 0
        if home_goals['home_gc'] is not None:
            self.gc += home_goals['home_gc']
        if away_goals['away_gc'] is not None:
            self.gc += away_goals['away_gc']

        self.points = self._points()
        self.save()

    def _points(self):
        return (
            self.won * MATCH_WON_POINTS
            + self.tie * MATCH_TIE_POINTS
            + self.lost * MATCH_LOST_POINTS
        )


class League(models.Model):
    """Custom league metadata."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    created = models.DateTimeField(default=now)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='LeagueMember'
    )

    objects = LeagueManager()

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'tournament'), ('slug', 'tournament'))

    def __str__(self):
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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=now)

    class Meta:
        unique_together = ('user', 'league')

    def __str__(self):
        return str(self.user)


@receiver(post_save, sender=Match, dispatch_uid="update-scores")
def update_related_predictions(sender, instance, **kwargs):
    """Update score for predictions related to the changed match."""
    home_goals = instance.home_goals
    away_goals = instance.away_goals
    predictions = instance.prediction_set

    if not instance.finished:
        # update starred field for predictions (only while not played)
        predictions.update(starred=instance.starred, score=0)
        return

    # reset predictions
    predictions.update(score=0)

    # update unpredicted predictions with default values, taken from the
    # user's preferences (if any)

    def default_prediction_goals(side):
        return (
            EgaUser.objects.filter(pk=OuterRef('user_id'))
            .annotate(
                goals=Cast(
                    'preferences__default_prediction__%s_goals' % side,
                    models.PositiveIntegerField(),
                )
            )
            .values('goals')[:1]
        )

    def default_prediction_penalties():
        return (
            EgaUser.objects.filter(pk=OuterRef('user_id'))
            .annotate(
                penalties=Case(
                    When(
                        preferences__default_prediction__penalties='L',
                        then=Value('L'),
                    ),
                    When(
                        preferences__default_prediction__penalties='V',
                        then=Value('V'),
                    ),
                    When(
                        preferences__default_prediction__penalties='',
                        then=Value(''),
                    ),
                    default=Value(''),
                )
            )
            .values('penalties')[:1]
        )

    predictions.filter(
        home_goals__isnull=True,
        away_goals__isnull=True,
        user__preferences__default_prediction__isnull=False,
    ).update(
        source='preferences',
        home_goals=Subquery(default_prediction_goals('home')),
        away_goals=Subquery(default_prediction_goals('away')),
        penalties=Subquery(default_prediction_penalties()),
    )

    # update exact predictions
    predictions.filter(home_goals=home_goals, away_goals=away_goals).update(
        score=EXACTLY_MATCH_POINTS
    )

    # update winner predictions
    if home_goals > away_goals:
        predictions.exclude(
            home_goals=home_goals, away_goals=away_goals
        ).filter(home_goals__gt=F('away_goals')).update(
            score=WINNER_MATCH_POINTS
        )
    elif home_goals < away_goals:
        predictions.exclude(
            home_goals=home_goals, away_goals=away_goals
        ).filter(home_goals__lt=F('away_goals')).update(
            score=WINNER_MATCH_POINTS
        )
    else:
        predictions.exclude(
            home_goals=home_goals, away_goals=away_goals
        ).filter(home_goals=F('away_goals'), home_goals__isnull=False).update(
            score=WINNER_MATCH_POINTS
        )

    # update starred predictions
    predictions.filter(score__gt=0, starred=True).update(score=F('score') + 1)

    # update penalties predictions
    penalties = (
        instance.pk_home_goals is not None
        and instance.pk_away_goals is not None
    )
    if penalties:
        ties = predictions.filter(score__gt=0, home_goals=F('away_goals'))
        if instance.pk_home_goals > instance.pk_away_goals:
            ties.filter(penalties='L').update(score=F('score') + 1)
        else:
            ties.filter(penalties='V').update(score=F('score') + 1)


@receiver(post_save, sender=Match, dispatch_uid="update-stats")
def update_related_stats(sender, instance, **kwargs):
    """Update team stats related to the changed match."""
    if instance.home and instance.away:
        for team in (instance.home, instance.away):
            stats, created = TeamStats.objects.get_or_create(
                team=team, tournament=instance.tournament
            )
            stats.sync()
