# -*- coding: utf-8 -*-
import os

import feedparser
from django.test import TestCase


class PullNewsTestCase(TestCase):
    """Tests for canchallena helper to pull news from atom feed."""

    def setUp(self):
        # remote or local test?
        self.test_remote = os.getenv('FENICS_TEST_REMOTE', None)
        if self.test_remote:
            self.url = 'http://www.canchallena.com/herramientas/rss'
        else:
            cwd = os.path.dirname(os.path.realpath(__file__))
            self.url = os.path.join(cwd, 'samples/canchallena.xml')

    def test_feed_entries(self):
        """Check the required field values are available in the feed."""
        feed = feedparser.parse(self.url)
        self.assertIsNotNone(feed.get('entries', None))

        news_available = False
        required = ['updated', 'title', 'link', 'summary']
        for e in feed['entries']:
            for k in required:
                self.assertIsNotNone(e.get(k, None))
        
            tags = [t['term'] for t in e.get('tags', [])]
            if u'Primera División' in tags:
               news_available = True

        self.assertTrue(news_available)
