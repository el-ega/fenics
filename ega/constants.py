# -*- coding: utf-8 -*-

from __future__ import unicode_literals


EL_EGA_NO_REPLY = 'noreply@el-ega.com.ar'

EMAILS_PLACEHOLDER = 'Los emails de tus amigos, separados por coma'

INVITE_BODY = """Hola!

Estoy jugando en el Ega, donde pronosticamos torneos varios de fútbol.
Estamos a full arrancando con el mundial Brasil 2014, estaría bueno si
venís a participar conmigo.

Podés unirte siguiendo el link: %(url)s

Saludos!
"""

INVITE_SUBJECT = 'Sumate a "el Ega"'

LEAGUE_JOIN_CHOICES = [
    ('tweet', 'Link followed from tweet.'),
    ('email', 'Link followed from email.'),
    ('self', 'User joined a league by himself.'),
]


# Game settings

DEFAULT_TOURNAMENT = 'brasil-2014'

NEXT_MATCHES_DAYS = 7
HOURS_TO_DEADLINE = 2

EXACTLY_MATCH_POINTS = 3
WINNER_MATCH_POINTS = 1
STARRED_MATCH_POINTS = 1

MATCH_WON_POINTS = 3
MATCH_TIE_POINTS = 1
MATCH_LOST_POINTS = 0

RANKING_TEAMS_PER_PAGE = 10
