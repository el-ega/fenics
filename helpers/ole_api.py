import datetime
import re

from pyquery import PyQuery


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
        data = self.columns[8].text
        return data

    @property
    def match_date(self):
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
        return self.columns[10].text

    @property
    def stadium(self):
        return self.columns[9].text

    @property
    def home_team(self):
        return self.columns[1].find('a').find('img').get('alt')
        
    @property
    def away_team(self):
        return self.columns[6].find('a').find('img').get('alt')

    @property
    def home_score(self):
        try:
            data = int(self.columns[3].find('p').text)
        except ValueError:
            data = None
        return data

    @property
    def away_score(self):
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

    @property
    def num_fechas(self):
        return len(self.fechas)

    def get_fecha(self, fecha):
        fecha = self.fechas[fecha - 1]
        tbody = fecha.find('tbody')
        matches = tbody.findall('tr')

        return [Match(data) for data in matches]

