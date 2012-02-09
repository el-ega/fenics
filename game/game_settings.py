from django.conf import settings

HOURS_TO_DEADLINE = getattr(settings, "GAME_HOURS_TO_DEADLINE", 2)
EXACTLY_MATCH_POINTS = getattr(settings, "GAME_EXACTLY_MATCH_POINTS", 3)
WINNER_MATCH_POINTS = getattr(settings, "GAME_WINNER_MATCH_POINTS", 1)
STARRED_MATCH_POINTS = getattr(settings, "GAME_STARRED_MATCH_POINTS", 1)
