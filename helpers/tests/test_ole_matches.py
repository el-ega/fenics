# -*- coding: utf-8 -*-
import os

from django.test import TestCase
from pyquery import PyQuery


class PullMatchInfoTestCase(TestCase):
    """Tests for ole helper to pull matches info from fixture page."""

    def setUp(self):
        # remote or local test?
        self.test_remote = os.getenv('FENICS_TEST_REMOTE', None)
        if self.test_remote:
            url = 'http://www.ole.com.ar/estadisticas/futbol/primera-division.html'
            self.pq = PyQuery(url=url)
        else:
            cwd = os.path.dirname(os.path.realpath(__file__))
            filename = os.path.join(cwd, 'samples/fixture.html')
            self.pq = PyQuery(filename=filename)

    def test_fechas_available(self):
        """Check fechas count is correct."""
        fechas = self.pq('table[id^=fecha_]')
        # 19 fechas + promocion
        self.assertEqual(len(fechas), 21)

    def test_matches_per_fecha(self):
        """Check for 10 matches per fechas."""
        fechas = self.pq('table[id^=fecha_]')
        # 19 fechas + promocion
        for fecha in fechas[:19]:
            tbody = fecha.find('tbody')
            matches = tbody.findall('tr')
            self.assertEqual(len(matches), 10)

    def test_fecha_1_match_1(self):
        """Check first match of fecha 1 for structure."""
        fecha = self.pq('table[id=fecha_1]')
        tbody = fecha.find('tbody')
        match = tbody.find('tr')[0]

        match_fields = match.getchildren()
        home_team = match_fields[1].find('a').find('img').get('alt')
        away_team = match_fields[6].find('a').find('img').get('alt')
        home_score = match_fields[3].find('p').text
        away_score = match_fields[4].find('p').text

        self.assertEqual(home_team, 'Boca')
        self.assertEqual(away_team, 'Olimpo')
        self.assertEqual(home_score, '2')
        self.assertEqual(away_score, '0')
