import logging
import os

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from ega.models import Match, Team, Tournament

logger = logging.getLogger(__name__)

API_BASE = 'https://api.football-data.org/v4'
IN_PLAY = frozenset({'IN_PLAY', 'PAUSED'})
FINISHED = frozenset({'FINISHED', 'AWARDED'})
SUSPENDED = frozenset({'SUSPENDED', 'POSTPONED', 'CANCELLED'})


class Command(BaseCommand):
    help = 'Fetch live/recent match scores from football-data.org and update local records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tournament',
            default='mundial-2026',
            help='Tournament slug to update (default: mundial-2026)',
        )
        parser.add_argument(
            '--competition',
            default='WC',
            help='football-data.org competition code (default: WC)',
        )
        parser.add_argument(
            '--api-key',
            dest='api_key',
            help='API key (overrides FOOTBALL_DATA_API_KEY in settings/env)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving',
        )

    def handle(self, *args, **options):
        api_key = (
            options['api_key']
            or getattr(settings, 'FOOTBALL_DATA_API_KEY', None)
            or os.environ.get('FOOTBALL_DATA_API_KEY')
        )
        if not api_key:
            raise CommandError(
                'No API key found. Pass --api-key, or set FOOTBALL_DATA_API_KEY '
                'in settings.py / local_settings.py, or export it as an env var.'
            )

        try:
            tournament = Tournament.objects.get(slug=options['tournament'])
        except Tournament.DoesNotExist:
            raise CommandError(f"Tournament not found: '{options['tournament']}'")

        url = f"{API_BASE}/competitions/{options['competition']}/matches"
        try:
            response = requests.get(
                url,
                headers={'X-Auth-Token': api_key},
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CommandError(f'API request failed: {exc}')

        api_matches = response.json().get('matches', [])
        if options['verbosity'] >= 1:
            self.stdout.write(f'Fetched {len(api_matches)} matches from API')

        updated = 0
        skipped = 0

        for entry in api_matches:
            status = entry.get('status', '')
            if status not in (IN_PLAY | FINISHED | SUSPENDED):
                continue

            home_tla = (entry.get('homeTeam') or {}).get('tla', '').upper()
            away_tla = (entry.get('awayTeam') or {}).get('tla', '').upper()

            utc_date = entry.get('utcDate')
            match_date = parse_datetime(utc_date).date() if utc_date else None

            try:
                home_team = Team.objects.get(code__iexact=home_tla, tournament=tournament)
                away_team = Team.objects.get(code__iexact=away_tla, tournament=tournament)
            except Team.DoesNotExist:
                if options['verbosity'] >= 2:
                    self.stderr.write(f'  Team not found: {home_tla} or {away_tla}')
                skipped += 1
                continue

            qs = Match.objects.filter(tournament=tournament, home=home_team, away=away_team)
            if match_date:
                qs = qs.filter(when__date=match_date)
            try:
                match = qs.get()
            except Match.DoesNotExist:
                if options['verbosity'] >= 2:
                    self.stderr.write(f'  Match not found: {home_tla} vs {away_tla}')
                skipped += 1
                continue
            except Match.MultipleObjectsReturned:
                self.stderr.write(
                    f'  Ambiguous match (multiple rows): {home_tla} vs {away_tla} on {match_date}'
                )
                skipped += 1
                continue

            if match.finished:
                continue

            if self._apply_update(match, status, entry, options['dry_run'], options['verbosity']):
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'Done: {updated} updated, {skipped} skipped.')
        )

    def _apply_update(self, match, status, entry, dry_run, verbosity):
        changed = False
        score = entry.get('score') or {}

        if status in SUSPENDED:
            if not match.suspended:
                match.suspended = True
                changed = True
        else:
            # For knockout matches that go to ET, regularTime holds the 90-min score;
            # otherwise fullTime is the authoritative current/final score.
            regular = score.get('regularTime') or {}
            full = score.get('fullTime') or {}
            penalties = score.get('penalties') or {}

            h = regular.get('home') if regular.get('home') is not None else full.get('home')
            a = regular.get('away') if regular.get('away') is not None else full.get('away')
            pk_h = penalties.get('home')
            pk_a = penalties.get('away')

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

            if status in FINISHED and not match.finished:
                match.finished = True
                changed = True

        if not changed:
            return False

        score_str = (
            f'{match.home_goals}-{match.away_goals}'
            if match.home_goals is not None
            else '?-?'
        )
        label = f'{match.home} {score_str} {match.away} [{status}]'
        if verbosity >= 1:
            prefix = '[DRY RUN] ' if dry_run else ''
            self.stdout.write(f'  {prefix}{label}')

        if not dry_run:
            with transaction.atomic():
                match.save()

        return True
