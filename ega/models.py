from django.contrib.auth.models import User
from django.db import models


class Tournament(models.Model):
    """Tournament metadata."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    teams = models.ManyToManyField('Team', verbose_name=_('equipos'))
    published = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class Team(models.Model):
    """Team metadata."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(upload_to='teams/logos', null=True, blank=True)

    def __unicode__(self):
        return self.name


class Match(models.Model):
    """Match metadata."""
    home = models.ForeignKey(Team, related_name='home_games')
    visitor = models.ForeignKey(Team, related_name='away_games')
    home_goals = models.IntegerField(null=True, blank=True)
    visitor_goals = models.IntegerField(null=True, blank=True)

    tournament = models.ForeignKey('Tournament')
    when = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    referee = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return u"%s: %s vs %s" % (
            self.tournament, self.home.name, self.away.name)


class Card(models.Model):
    """User prediction for a match."""
    user = models.ForeignKey(User)
    match = models.ForeignKey('Match')

    home_goals = models.IntegerField(null=True, blank=True)
    away_goals = models.IntegerField(null=True, blank=True)
    starred = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    exact = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'match')

    def __unicode__(self):
        return u"%s: %s vs %s" % (self.user, self.match)


class League(models.Model):
    """Custom league metadata."""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    tournament = models.ForeignKey('Tournament')
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return u"%s - $s" % (self.owner, self.name)
