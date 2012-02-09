# -*- coding: utf-8 -*-
import math

from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _

import game_settings


class Team(models.Model):
    name = models.CharField(_('Nombre'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True)
    logo = models.ImageField(_('Imagen'), upload_to='teams/logos', null=True,
                             blank=True)

    class Meta:
        verbose_name = _('Equipo')

    def __unicode__(self):
        return self.name


class Tournament(models.Model):
    name = models.CharField(_('Nombre'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True)
    teams = models.ManyToManyField('Team', verbose_name=_('Equipos'))
    publish = models.BooleanField(_('Publicar'), default=True)

    class Meta:
        verbose_name = _('Torneo')

    def __unicode__(self):
        return self.name


class MatchGroup(models.Model):
    tournament = models.ForeignKey('Tournament', verbose_name=_('Torneo'))
    name = models.CharField(_('Nombre'), max_length=200)

    class Meta:
        verbose_name = _('Grupo de partidos')
        verbose_name_plural = _('Grupos de partidos')

    def __unicode__(self):
        return "%s - %s" % (self.tournament.name, self.name)


class Match(models.Model):
    group = models.ForeignKey('MatchGroup')
    home = models.ForeignKey(Team, verbose_name=_('Equipo local'),
                             related_name='home_game_set',)
    away = models.ForeignKey(Team, verbose_name=_('Equipo visitante'),
                             related_name='away_game_set',)
    home_goals = models.IntegerField(_('Goles equipo local'), null=True,
                                     blank=True)
    away_goals = models.IntegerField(_('Goles equipo visitante'), null=True,
                                     blank=True)
    date = models.DateTimeField(_('Fecha del partido'), null=True, blank=True)
    approved = models.BooleanField(_('Aprobado'), default=False)

    class Meta:
        verbose_name = _('Partido')

    def __unicode__(self):
        return "%s - %s: %s vs %s" % (self.group.tournament.name,
                                      self.group.name, self.home.name,
                                      self.away.name)

    @property
    def deadline(self):
        """Return deadline datetime or None if match date is not set."""
        ret = None
        if self.date:
            ret = self.date - timedelta(hours=game_settings.HOURS_TO_DEADLINE)
        return ret

    def save(self, *args, **kwargs):
        super(Match, self).save(*args, **kwargs)
        if self.approved:
            cards = self.card_set.all()
            for card in cards:
                # update card score
                card.update_score()
                # update user position
                position, created = UserPosition.objects.get_or_create(
                    tournament=self.group.tournament, user=card.user)
                position.update()


class Card(models.Model):
    user = models.ForeignKey(User, verbose_name=_('Usuario'))
    starred = models.BooleanField(_('Partido estrella?'), default=False)
    match = models.ForeignKey('Match', verbose_name=_('Partido'))
    home_goals = models.IntegerField(_('Goles equipo local'), null=True,
                                     blank=True)
    away_goals = models.IntegerField(_('Goles equipo visitante'), null=True,
                                     blank=True)
    score = models.IntegerField(_('Puntos'), null=True, blank=True)

    class Meta:
        verbose_name = _('Tarjeta')
        unique_together = ('user', 'match')

    def __unicode__(self):
        return "%s: %s vs %s" % (str(self.user), self.match.home.name,
                                 self.match.away.name)

    def update_score(self):
        """ Updates the score from the real result."""
        home = self.match.home_goals
        away = self.match.away_goals

        if home is None or away is None:
            self.score = 0
        elif self.home_goals == home and self.away_goals == away:
            self.score = game_settings.EXACTLY_MATCH_POINTS
        elif self.home_goals > self.away_goals and home > away:
            self.score = game_settings.WINNER_MATCH_POINTS
        elif self.home_goals < self.away_goals and home < away:
            self.score = game_settings.WINNER_MATCH_POINTS
        elif self.home_goals == self.away_goals and home == away:
            self.score = game_settings.WINNER_MATCH_POINTS
        else:
            self.score = 0

        if self.score and self.starred:
            self.score = self.score + game_settings.STARRED_MATCH_POINTS

        self.save()


class UserPosition(models.Model):
    tournament = models.ForeignKey('Tournament', verbose_name=_('Torneo'))
    user = models.ForeignKey(User, verbose_name=_('Usuario'))
    points = models.IntegerField(_('Puntos'), default=0)

    class Meta:
        verbose_name = _('Posiciones de usuario')
        verbose_name_plural = _('Posiciones de usuario')
        ordering = ['-points']
        unique_together = ('user', 'tournament')

    def update(self):
        """Update user position according to card scores."""
        cards = self.user.card_set.filter(
            match__group__tournament=self.tournament)
        score = cards.aggregate(total=Sum('score'))
        self.points = score['total']
        self.save()


class LeagueInvitation(models.Model):
    league = models.ForeignKey('FriendsLeague', verbose_name=_('Liga'))
    accepted = models.NullBooleanField(_('Aceptada?'))
    email = models.EmailField(_('Email'))

    class Meta:
        verbose_name = _('Invitacion')
        verbose_name_plural = _('Invitaciones')

    def __unicode__(self):
        return self.mail

    @property
    def user(self):
        try:
            ret = User.objects.get(email=self.email)
        except User.DoesNotExist:
            ret = None
        return ret


class FriendsLeague(models.Model):
    name = models.CharField(_('Nombre'), max_length=200)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True)
    tournament = models.ForeignKey('Tournament', verbose_name=_('Torneo'))
    owner = models.ForeignKey(User, verbose_name=_('Creador'))
    invites = models.ManyToManyField(LeagueInvitation,
                                     verbose_name=_('Usuarios'))

    class Meta:
        verbose_name = _('Liga de Amigos')
        verbose_name_plural = _('Ligas de Amigos')

    def __unicode__(self):
        return self.name
