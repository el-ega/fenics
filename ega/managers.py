from django.db import models

from ega.constants import DEFAULT_TOURNAMENT


class PredictionManager(models.Manager):
    """Prediction manager.

    Forces preload of related team and team stats instances.
    """

    def get_queryset(self):
        return super(
            PredictionManager, self).get_queryset().select_related(
                'match__home', 'match__away')


class LeagueManager(models.Manager):
    """League manager."""

    def current(self):
        qs = self.get_queryset().filter(tournament__slug=DEFAULT_TOURNAMENT)
        return qs
