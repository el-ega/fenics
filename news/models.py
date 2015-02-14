from django.db import models


class News(models.Model):
    title = models.CharField(max_length=256)
    source = models.CharField(max_length=64, blank=True)
    published = models.DateTimeField()
    summary = models.TextField()
    link = models.URLField()

    class Meta:
        verbose_name = 'News'
        verbose_name_plural = 'News'
        ordering = ['-published']

    def __unicode__(self):
        return self.title
