from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from ega import settings as game_settings


class Tournament(models.Model):
    """Tournament metadata."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    teams = models.ManyToManyField('Team')
    published = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def next_matches(self, days=game_settings.NEXT_MATCHES_DAYS):
        """Return matches in the next days."""
        now = datetime.utcnow()
        until = now + timedelta(days=days)
        return self.match_set.filter(when__range=(now, until))


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
            Q(away=self)|Q(home=self), date__lte=now)
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

    def __unicode__(self):
        return u"%s: %s vs %s" % (
            self.tournament, self.home.name, self.away.name)

    @property
    def deadline(self):
        """Return deadline datetime or None if match date is not set."""
        ret = None
        if self.when:
            ret = self.when - timedelta(hours=game_settings.HOURS_TO_DEADLINE)
        return ret


class Prediction(models.Model):
    """User prediction for a match."""
    user = models.ForeignKey(User)
    match = models.ForeignKey('Match')

    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)
    starred = models.BooleanField(default=False)

    score = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'match')

    def __unicode__(self):
        return u"%s: %s" % (self.user, self.match)

    def update_score(self):
        """Updates the score from the real result."""
        home = self.match.home_goals
        away = self.match.away_goals

        score = 0
        if home is None or away is None:
            score = 0
        elif self.home_goals == home and self.away_goals == away:
            score = game_settings.EXACTLY_MATCH_POINTS
        elif self.home_goals > self.away_goals and home > away:
            score = game_settings.WINNER_MATCH_POINTS
        elif self.home_goals < self.away_goals and home < away:
            score = game_settings.WINNER_MATCH_POINTS
        elif self.home_goals == self.away_goals and home == away:
            score = game_settings.WINNER_MATCH_POINTS

        if score and self.starred:
            score += game_settings.STARRED_MATCH_POINTS

        self.score = score
        self.save()


class League(models.Model):
    """Custom league metadata."""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    tournament = models.ForeignKey('Tournament')
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return u"%s - $s" % (self.owner, self.name)


@receiver(post_save, sender=Match, dispatch_uid="update-scores")
def update_related_predictions(sender, instance, **kwargs):
    """Update score for predictions related to the changed match."""
    predictions = instance.prediction_set.all()
    for prediction in predictions:
        prediction.update_score()
