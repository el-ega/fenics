import datetime
import re

from pyquery import PyQuery


#TODO: extend API to handle more tournaments


FIXTURE_URL = 'http://www.ole.com.ar/estadisticas/futbol/primera-division.html'


class Match(object):
    """Match data."""

    DATE_REGEXP = re.compile(r'(?P<day>\d+)\.(?P<month>\d+)\.(?P<year>\d+)')
    DATETIME_REGEXP = re.compile(r"""(?P<day>\d+)\.(?P<month>\d+)\.(?P<year>\d+)
                                 [^\d]+(?P<hour>\d+):(?P<minute>\d+)""",
                                 re.VERBOSE)

    def __init__(self, pq_data):
        self.columns = pq_data.getchildren()

    @property
    def status(self):
        """Return match status.

        Possible values:
            Finalizado|Primer Tiempo|Entretiempo|Segundo Tiempo
            or a future date.

        """
        data = self.columns[8].text
        return data

    @property
    def match_date(self):
        """Return the match datetime if available."""
        ret = None
        data = self.columns[8].text
        is_datetime = self.DATETIME_REGEXP.match(data)
        is_date = self.DATE_REGEXP.match(data)
        if is_datetime:
            date_dict = is_datetime.groupdict()
            date_dict = dict(((k, int(v)) for k, v in date_dict.iteritems()))
            ret = datetime.datetime(**date_dict)
        elif is_date:
            date_dict = is_date.groupdict()
            date_dict = dict(((k, int(v)) for k, v in date_dict.iteritems()))
            ret = datetime.datetime(**date_dict)
        return ret

    @property
    def referee(self):
        """Return referee information if available."""
        return self.columns[10].text

    @property
    def stadium(self):
        """Return stadium information if available."""
        return self.columns[9].text

    @property
    def home_team(self):
        """Return home team name."""
        return self.columns[1].find('a').find('img').get('alt')
        
    @property
    def away_team(self):
        """Return away team name."""
        return self.columns[6].find('a').find('img').get('alt')

    @property
    def home_score(self):
        """Return home team goals if available (ie, match already played)."""
        try:
            data = int(self.columns[3].find('p').text)
        except ValueError:
            data = None
        return data

    @property
    def away_score(self):
        """Return away team goals if available (ie, match already played)."""
        try:
            data = int(self.columns[4].find('p').text)
        except ValueError:
            data = None
        return data


class Fixture(object):
    """Fixture data from Ole."""

    def __init__(self):
        self.pq = PyQuery(url=FIXTURE_URL)
        self.fechas = self.pq('table[id^=fecha_]')
        self._current = 1

    @property
    def num_fechas(self):
        """Return the number of match groups."""
        # hard-coded for Primera Division
        return 19

    def get_fecha(self, fecha):
        """Return matches information for the given fecha."""
        fecha = self.fechas[fecha - 1]
        tbody = fecha.find('tbody')
        matches = tbody.findall('tr')

        return [Match(data) for data in matches]

    def get_teams(self):
        """Return names list of the teams in the tournament."""
        matches = self.get_fecha(1)
        teams = []
        for m in matches:
            teams.append(m.home_team)
            teams.append(m.away_team)
        return teams

    def __iter__(self):
        return self

    def next(self):
        if self._current <= self.num_fechas:
            fecha = self.get_fecha(self._current)
            self._current += 1
            return fecha
        raise StopIteration
