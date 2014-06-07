from django.db import models
from django.utils.translation import ugettext_lazy as _


class News(models.Model):
    title = models.CharField(max_length=256)
    published = models.DateTimeField()
    summary = models.TextField()
    link = models.URLField()

    class Meta:
        verbose_name = 'News'
        verbose_name_plural = 'News'
        ordering = ['-published']

    def __unicode__(self):
        return self.title
