from collections import defaultdict

from ega.constants import (
    MATCH_LOST_POINTS,
    MATCH_TIE_POINTS,
    MATCH_WON_POINTS,
    WORLD_CUP_2026_BRACKET,
    WORLD_CUP_2026_GROUPS,
)


def tournament_format(tournament):
    configured = tournament.preferences.get('format') if tournament else None
    default = {}
    if tournament and tournament.slug == 'worldcup-2026':
        default = {
            'groups': WORLD_CUP_2026_GROUPS,
            'bracket': WORLD_CUP_2026_BRACKET,
        }
    if configured:
        default.update(configured)
    return default


def build_predicted_standings(tournament, predictions):
    """Return user-predicted group standings and best third-place teams."""
    stats = defaultdict(lambda: (0, 0, 0))
    zones = {
        s.team_id: s.zone
        for s in tournament.teamstats_set.exclude(zone='').only(
            'team_id', 'zone'
        )
    }

    for prediction in predictions:
        match = prediction.match
        if not match.home_id or not match.away_id:
            continue

        home_goals = prediction.home_goals
        away_goals = prediction.away_goals
        if home_goals is None or away_goals is None:
            continue

        home_points = away_points = MATCH_TIE_POINTS
        if home_goals > away_goals:
            home_points = MATCH_WON_POINTS
            away_points = MATCH_LOST_POINTS
        elif home_goals < away_goals:
            home_points = MATCH_LOST_POINTS
            away_points = MATCH_WON_POINTS

        home_update = (home_points, home_goals - away_goals, home_goals)
        away_update = (away_points, away_goals - home_goals, away_goals)
        stats[match.home_id] = tuple(
            map(sum, zip(stats[match.home_id], home_update))
        )
        stats[match.away_id] = tuple(
            map(sum, zip(stats[match.away_id], away_update))
        )

    grouped = defaultdict(list)
    for team_id, values in stats.items():
        grouped[zones.get(team_id, '')].append((team_id, values))

    standings = {}
    third_places = []
    for zone in sorted(grouped):
        teams = sorted(grouped[zone], key=lambda i: i[1], reverse=True)
        for index, (team_id, values) in enumerate(teams, start=1):
            label = '{}{}'.format(index, zone)
            standings[label] = team_id
            if index == 3:
                third_places.append(
                    {
                        'label': label,
                        'team_id': team_id,
                        'zone': zone,
                        'points': values[0],
                        'goal_difference': values[1],
                        'goals_for': values[2],
                    }
                )

    third_places.sort(
        key=lambda row: (
            row['points'],
            row['goal_difference'],
            row['goals_for'],
            row['zone'],
        ),
        reverse=True,
    )
    return standings, third_places


def projected_bracket(tournament, user):
    fmt = tournament_format(tournament)
    bracket = fmt.get('bracket') or []
    if not bracket:
        return []

    teams = {team.id: team for team in tournament.teams.all()}
    standings = user.predicted_ranking(tournament)
    third_places = user.predicted_third_places(tournament)
    third_by_zone = {
        row['zone']: teams.get(row['team_id'], row['label'])
        for row in third_places[:8]
    }

    return [
        {
            'match': match['match'],
            'round': match.get('round', ''),
            'home': _resolve_slot(
                match['home'], standings, teams, third_by_zone
            ),
            'away': _resolve_slot(
                match['away'], standings, teams, third_by_zone
            ),
            'home_slot': match['home'],
            'away_slot': match['away'],
        }
        for match in bracket
    ]


def _resolve_slot(slot, standings, teams, third_by_zone):
    if slot.startswith('3'):
        zones = slot[1:].split('/')
        for zone in zones:
            if zone in third_by_zone:
                return third_by_zone[zone]
        return slot

    team_id = standings.get(slot)
    if team_id is None:
        return slot
    return teams.get(team_id, slot)
