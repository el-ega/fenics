from django.db import models


class PredictionManager(models.Manager):
    """Prediction manager.

    Forces preload of related team and team stats instances.
    """

    def get_queryset(self):
        return super(
            PredictionManager, self).get_queryset().select_related(
                'match__home', 'match__away')
