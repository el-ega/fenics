# -*- coding: utf-8 -*-

EMAILS_PLACEHOLDER = 'Los emails de tus amigos, separados por coma'

INVITE_BODY = """Hola!

Estoy jugando en el Ega, pronosticando los resultados del
Torneo de Transición 2014, estaría bueno si venís a participar conmigo.
%(extra_text)s
Podés unirte siguiendo el link: %(url)s

Saludos!
%(inviter)s"""

INVITE_LEAGUE = """
Para hacer las cosas más interesantes, creé una liga de amigos, en donde vamos
a tener una tabla de posiciones separada de la general y vamos a poder comentar
y discutir opiniones entre nosotros. Esta liga se llama %(league_name)s.
"""

INVITE_SUBJECT = 'Sumate a "el Ega"'

LEAGUE_JOIN_CHOICES = [
    ('tweet', 'Link followed from tweet.'),
    ('email', 'Link followed from email.'),
    ('self', 'User joined a league by himself.'),
]


# Game settings

DEFAULT_TOURNAMENT = 'qatar-2022'

NEXT_MATCHES_DAYS = 200
HOURS_TO_DEADLINE = 0

EXACTLY_MATCH_POINTS = 3
WINNER_MATCH_POINTS = 1
STARRED_MATCH_POINTS = 1

MATCH_WON_POINTS = 3
MATCH_TIE_POINTS = 1
MATCH_LOST_POINTS = 0

HISTORY_MATCHES_PER_PAGE = 13
RANKING_TEAMS_PER_PAGE = 10

# TODO: use knockout match placeholders?
ROUND16_MATCHES = (
    ('1A', '2B'),
    ('1C', '2D'),
    ('1D', '2C'),
    ('1B', '2A'),
    ('1E', '2F'),
    ('1G', '2H'),
    ('1F', '2E'),
    ('1H', '2G'),
)
