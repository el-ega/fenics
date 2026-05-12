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

DEFAULT_TOURNAMENT = 'worldcup-2026'

NEXT_MATCHES_DAYS = 300
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

WORLD_CUP_2026_GROUPS = tuple('ABCDEFGHIJKL')

WORLD_CUP_2026_BRACKET = (
    {
        'match': 73,
        'round': 'Round of 32',
        'home': '2A',
        'away': '2B',
    },
    {
        'match': 74,
        'round': 'Round of 32',
        'home': '1E',
        'away': '3A/B/C/D/F',
    },
    {
        'match': 75,
        'round': 'Round of 32',
        'home': '1F',
        'away': '2C',
    },
    {
        'match': 76,
        'round': 'Round of 32',
        'home': '1C',
        'away': '2F',
    },
    {
        'match': 77,
        'round': 'Round of 32',
        'home': '1I',
        'away': '3C/D/F/G/H',
    },
    {
        'match': 78,
        'round': 'Round of 32',
        'home': '2E',
        'away': '2I',
    },
    {
        'match': 79,
        'round': 'Round of 32',
        'home': '1A',
        'away': '3C/E/F/H/I',
    },
    {
        'match': 80,
        'round': 'Round of 32',
        'home': '1L',
        'away': '3E/H/I/J/K',
    },
    {
        'match': 81,
        'round': 'Round of 32',
        'home': '1D',
        'away': '3B/E/F/I/J',
    },
    {
        'match': 82,
        'round': 'Round of 32',
        'home': '1G',
        'away': '3A/E/H/I/J',
    },
    {
        'match': 83,
        'round': 'Round of 32',
        'home': '2K',
        'away': '2L',
    },
    {
        'match': 84,
        'round': 'Round of 32',
        'home': '1H',
        'away': '2J',
    },
    {
        'match': 85,
        'round': 'Round of 32',
        'home': '1B',
        'away': '3E/F/G/I/J',
    },
    {
        'match': 86,
        'round': 'Round of 32',
        'home': '1J',
        'away': '2H',
    },
    {
        'match': 87,
        'round': 'Round of 32',
        'home': '1K',
        'away': '3D/E/I/J/L',
    },
    {
        'match': 88,
        'round': 'Round of 32',
        'home': '2D',
        'away': '2G',
    },
)
