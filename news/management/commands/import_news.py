# -*- coding: utf-8 -*-
import datetime

import feedparser

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import make_aware

from news.models import News


class Command(BaseCommand):
    help = 'Import news from feed'

    def handle(self, *args, **options):
        for source, feed_url in settings.NEWS_FEEDS:
            feed = feedparser.parse(feed_url)

            for entry in feed['entries']:
                news_date = make_aware(
                    datetime.datetime(
                        year=entry.updated_parsed.tm_year,
                        month=entry.updated_parsed.tm_mon,
                        day=entry.updated_parsed.tm_mday,
                        hour=entry.updated_parsed.tm_hour,
                        minute=entry.updated_parsed.tm_min,
                    )
                )

                if len(entry['link']) > 200:
                    continue

                if not News.objects.filter(
                    title=entry['title'], source=source, published=news_date
                ):
                    try:
                        news = News.objects.create(
                            title=entry['title'],
                            source=source,
                            published=news_date,
                            summary=entry['summary'],
                            link=entry['link'],
                        )
                    except:
                        # ignore for now
                        pass
