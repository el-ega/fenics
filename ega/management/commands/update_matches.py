from datetime import datetime

import requests
from pyquery import PyQuery as pq

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ega.models import Match, Team, Tournament


SOURCE_URL = (
    'https://cdnmd.lavoz.com.ar/sites/default/files/Datafactory/html/v3/'
    'htmlCenter/data/deportes/futbol/mundial/pages/es/fixture.html'
)

# Source uses abbreviated/alternate Spanish names for some teams
TEAM_NAME_MAP = {
    'A. Saudita': 'Arabia Saudita',
    'Bosnia-Herz.': 'Bosnia y Herzegovina',
    'C. de Marfil': 'Costa de Marfil',
    'Catar': 'Qatar',
    'N. Zelanda': 'Nueva Zelanda',
    'R. Checa': 'República Checa',
    'R. de Corea': 'Corea del Sur',
    'USA': 'Estados Unidos',
}

# Container CSS classes signalling an active (in-progress) match
IN_PROGRESS = frozenset({'status-half', 'status-inPlay', 'status-extraTime', 'status-penalties'})
FINISHED = 'status-finished'
SUSPENDED = 'status-suspended'


class Command(BaseCommand):
    help = 'Fetch live/recent World Cup scores from Datafactory and update local records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tournament',
            default='worldcup-2026',
            help='Tournament slug to update (default: worldcup-2026)',
        )
        parser.add_argument(
            '--url',
            default=SOURCE_URL,
            help='Source fixture HTML URL',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving',
        )

    def handle(self, *args, **options):
        try:
            tournament = Tournament.objects.get(slug=options['tournament'])
        except Tournament.DoesNotExist:
            raise CommandError(f"Tournament not found: '{options['tournament']}'")

        try:
            response = requests.get(
                options['url'],
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CommandError(f'Failed to fetch fixture page: {exc}')

        response.encoding = 'utf-8'
        d = pq(response.text)
        containers = d('.mc-matchContainer')
        if options['verbosity'] >= 1:
            self.stdout.write(f'Fetched {len(containers)} match containers')

        updated = 0
        skipped = 0

        for el in containers:
            m = pq(el)
            classes = set((m.attr('class') or '').split())

            is_finished = FINISHED in classes
            is_in_progress = bool(classes & IN_PROGRESS)
            is_suspended = SUSPENDED in classes

            if not (is_finished or is_in_progress or is_suspended):
                continue

            home_raw = m('.local .equipo').text().strip()
            away_raw = m('.visitante .equipo').text().strip()
            home_name = TEAM_NAME_MAP.get(home_raw, home_raw)
            away_name = TEAM_NAME_MAP.get(away_raw, away_raw)

            # Skip unresolved knockout placeholders
            if not home_name or not away_name or _is_placeholder(home_name) or _is_placeholder(away_name):
                skipped += 1
                continue

            match_date = _parse_date(m)

            try:
                home_team = Team.objects.get(name=home_name, tournament=tournament)
                away_team = Team.objects.get(name=away_name, tournament=tournament)
            except Team.DoesNotExist:
                if options['verbosity'] >= 2:
                    self.stderr.write(f'  Team not found: "{home_name}" or "{away_name}"')
                skipped += 1
                continue

            qs = Match.objects.filter(tournament=tournament, home=home_team, away=away_team)
            if match_date:
                qs = qs.filter(when__date=match_date)
            try:
                match = qs.get()
            except Match.DoesNotExist:
                if options['verbosity'] >= 2:
                    self.stderr.write(f'  Match not found: {home_name} vs {away_name}')
                skipped += 1
                continue
            except Match.MultipleObjectsReturned:
                self.stderr.write(f'  Ambiguous match: {home_name} vs {away_name} on {match_date}')
                skipped += 1
                continue

            if match.finished:
                continue

            if _apply_update(match, m, is_finished, is_suspended, options, self.stdout, self.stderr):
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'Done: {updated} updated, {skipped} skipped.')
        )


def _is_placeholder(name):
    """True for unresolved knockout slot names like 'Ganador partido 73'."""
    return name.startswith(('Ganador ', 'Perdedor ', '1 Grupo ', '2 Grupo ', '3 Grupo '))


def _parse_date(m):
    original = m.attr('data-originaldate')
    if not original:
        return None
    try:
        return datetime.strptime(original, '%Y/%m/%d %H:%M').date()
    except ValueError:
        return None


def _goals(m, side):
    """Return goal count for 'local' or 'visitante', or None if not yet shown."""
    container = m(f'.{side} .resultado')
    if 'd-none' in (container.attr('class') or '').split():
        return None
    try:
        return int(container.find('.badge').text().strip())
    except (ValueError, TypeError):
        return None


def _pk_goals(m, side):
    """Return penalty goal count, or None if the penalties panel is hidden."""
    container = m(f'.{side} .penales')
    if 'd-none' in (container.attr('class') or '').split():
        return None
    try:
        return int(container.find('.badge').text().strip())
    except (ValueError, TypeError):
        return None


def _apply_update(match, m, is_finished, is_suspended, options, stdout, stderr):
    changed = False

    if is_suspended:
        if not match.suspended:
            match.suspended = True
            changed = True
    else:
        h = _goals(m, 'local')
        a = _goals(m, 'visitante')
        pk_h = _pk_goals(m, 'local')
        pk_a = _pk_goals(m, 'visitante')

        if h is not None and a is not None:
            if match.home_goals != h or match.away_goals != a:
                match.home_goals = h
                match.away_goals = a
                changed = True

        if pk_h is not None and pk_a is not None:
            if match.pk_home_goals != pk_h or match.pk_away_goals != pk_a:
                match.pk_home_goals = pk_h
                match.pk_away_goals = pk_a
                changed = True

        if is_finished and not match.finished:
            match.finished = True
            changed = True

    if not changed:
        return False

    score_str = (
        f'{match.home_goals}-{match.away_goals}'
        if match.home_goals is not None else '?-?'
    )
    status = 'FINISHED' if is_finished else ('SUSPENDED' if is_suspended else 'IN_PLAY')
    label = f'{match.home} {score_str} {match.away} [{status}]'

    if options['verbosity'] >= 1:
        prefix = '[DRY RUN] ' if options['dry_run'] else ''
        stdout.write(f'  {prefix}{label}')

    if not options['dry_run']:
        with transaction.atomic():
            match.save()

    return True
