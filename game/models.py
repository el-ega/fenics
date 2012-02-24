# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, Sum, Q
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

    def latest_matches(self, tournament=None):
        """Return team previously played matches."""
        now = datetime.now()
        matches = Match.objects.filter(Q(away=self)|Q(home=self), date__lte=now)
        return matches


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


class PlayableMatchesManager(models.Manager):
    """Manager that returns a queryset filtering open to play matches."""
    def get_query_set(self):
        now = datetime.now()
        deadline = now + timedelta(hours=game_settings.HOURS_TO_DEADLINE)
        available = now + timedelta(hours=game_settings.SHOW_HOURS_BEFORE)
        
        return super(PlayableMatchesManager, self).get_query_set().filter(
            date__gte=deadline, date__lte=available)


class Match(models.Model):
    group = models.ForeignKey('MatchGroup', verbose_name=_('Fecha'))
    location = models.CharField(_('Estadio'), max_length=200, blank=True)
    referee = models.CharField(_('Arbitro'), max_length=200, blank=True)
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

    objects = models.Manager()
    currently_playable = PlayableMatchesManager()

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

            # update team positions
            for team in [self.home, self.away]:
                position, created = TeamPosition.objects.get_or_create(
                                    tournament=self.group.tournament, team=team)
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
    exact = models.BooleanField(_('Exacto?'), default=False)

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
            self.exact = True
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
    points = models.IntegerField(_('Puntos (total)'), default=0)
    winner = models.IntegerField(_('Puntos (por acertar ganador)'), default=0)
    exact = models.IntegerField(_('Puntos (por resultado exacto)'), default=0)
    order = models.IntegerField(_('Posición'), default=0)

    class Meta:
        verbose_name = _('Posiciones de usuario')
        verbose_name_plural = _('Posiciones de usuario')
        ordering = ['-points', '-exact']
        unique_together = ('user', 'tournament')

    def _update_tournament(self):
        """"""
        positions = UserPosition.objects.filter(tournament=self.tournament)
        for order, position in enumerate(positions, 1):
            position.order = order
            position.save()

    def update(self):
        """Update user position according to card scores."""
        cards = self.user.card_set.filter(
            match__group__tournament=self.tournament)
        score = cards.aggregate(total=Sum('score'))
        self.points = score['total']
        self.exact = cards.filter(exact=True).count()
        self.winner = cards.count() - self.exact
        self.save()
        self._update_tournament()


class TeamPosition(models.Model):
    tournament = models.ForeignKey('Tournament', verbose_name=_('Torneo'))
    team = models.ForeignKey(Team, verbose_name=_('Equipo'))
    pts = models.IntegerField(_('Puntos'), default=0)
    pg = models.IntegerField(_('Partidos ganados'), default=0)
    pe = models.IntegerField(_('Partidos empatados'), default=0)
    pp = models.IntegerField(_('Partidos perdidos'), default=0)
    gf = models.IntegerField(_('Goles a favor'), default=0)
    gc = models.IntegerField(_('Goles en contra'), default=0)
    dg = models.IntegerField(_('Diferencia de gol'), default=0)
    order = models.IntegerField(_('Posición'), default=0)

    class Meta:
        verbose_name = _('Posiciones')
        verbose_name_plural = _('Posiciones')
        ordering = ['-pts', '-dg', '-gf', 'gc']
        unique_together = ('team', 'tournament')

    def _clear(self):
        """"""
        self.pts = 0
        self.pg = 0
        self.pe = 0
        self.pp = 0
        self.gf = 0
        self.gc = 0
        self.dg = 0

    def _update_tournament(self):
        """"""
        positions = TeamPosition.objects.filter(tournament=self.tournament)
        for order, position in enumerate(positions, 1):
            position.order = order
            position.save()

    def update(self):
        """Update team position according to approved match scores."""
        matches = Match.objects.filter(Q(home=self.team)|Q(away=self.team),
                                       group__tournament=self.tournament,
                                       home_goals__isnull=False,
                                       away_goals__isnull=False,
                                       approved=True)

        self._clear()
        for match in matches:
            if match.home == self.team:
                # as local
                self.gf += match.home_goals
                self.gc += match.away_goals
                if match.home_goals > match.away_goals:
                    self.pg += 1
                elif match.home_goals == match.away_goals:
                    self.pe += 1
                else:
                    self.pp += 1
            else:
                # as visitor
                self.gf += match.away_goals
                self.gc += match.home_goals
                if match.home_goals > match.away_goals:
                    self.pp += 1
                elif match.home_goals == match.away_goals:
                    self.pe += 1
                else:
                    self.pg += 1
        self.dg = self.gf - self.gc
        self.pts = self.pg * 3 + self.pe
        self.save()
        self._update_tournament()


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
