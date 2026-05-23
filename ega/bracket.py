from collections import defaultdict
import re

from ega.constants import (
    MATCH_LOST_POINTS,
    MATCH_TIE_POINTS,
    MATCH_WON_POINTS,
    WORLD_CUP_2026_BRACKET,
    WORLD_CUP_2026_GROUPS,
)


MATCH_NUMBER_RE = re.compile(r'(?:Match|Partido) (\d+)')


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
    third_candidates = _third_place_candidates(third_places, teams)
    used_third_zones = set()
    predictions = _predictions_by_match_number(tournament, user)
    projected = {}
    winners = {}
    losers = {}

    for match in bracket:
        home = _resolve_slot(
            match['home'],
            standings,
            teams,
            third_candidates,
            used_third_zones,
            winners,
            losers,
        )
        away = _resolve_slot(
            match['away'],
            standings,
            teams,
            third_candidates,
            used_third_zones,
            winners,
            losers,
        )
        prediction = predictions.get(match['match'])
        winner, loser = _predicted_result(home, away, prediction)
        row = {
            'match': match['match'],
            'round': match.get('round', ''),
            'home': home,
            'away': away,
            'home_slot': match['home'],
            'away_slot': match['away'],
            'prediction': prediction,
            'home_goals': prediction.home_goals if prediction else None,
            'away_goals': prediction.away_goals if prediction else None,
            'penalties': prediction.penalties if prediction else '',
            'winner': winner,
            'loser': loser,
            'resolved': winner is not None,
        }
        projected[match['match']] = row
        winners[match['match']] = winner
        losers[match['match']] = loser

    return [projected[match['match']] for match in bracket]


def projected_bracket_rounds(tournament, user):
    matches = projected_bracket(tournament, user)
    visual_order = _visual_match_order(matches)
    rounds = []
    by_round = {}
    for match in sorted(
        matches, key=lambda row: visual_order.get(row['match'], row['match'])
    ):
        round_name = match['round']
        if round_name not in by_round:
            group = {'round': round_name, 'matches': []}
            rounds.append(group)
            by_round[round_name] = group
        by_round[round_name]['matches'].append(match)
    return rounds


def _visual_match_order(matches):
    by_number = {match['match']: match for match in matches}
    first_round = [
        match
        for match in matches
        if not _source_match_numbers(match['home_slot'])
        and not _source_match_numbers(match['away_slot'])
    ]
    final = next(
        (match for match in matches if match['round'] == 'Final'), None
    )
    if final is None:
        leaves = [match['match'] for match in first_round]
    else:
        leaves = _leaf_match_numbers(final, by_number)
    leaf_positions = {
        match_number: index for index, match_number in enumerate(leaves)
    }
    fallback_position = len(leaf_positions)

    order = {}
    for match in matches:
        match_leaves = _leaf_match_numbers(match, by_number)
        positions = [
            leaf_positions[number]
            for number in match_leaves
            if number in leaf_positions
        ]
        if positions:
            order[match['match']] = min(positions)
        else:
            order[match['match']] = fallback_position + match['match']
    return order


def _leaf_match_numbers(match, by_number):
    sources = (
        _source_match_numbers(match['home_slot'])
        + _source_match_numbers(match['away_slot'])
    )
    if not sources:
        return [match['match']]

    leaves = []
    for source in sources:
        source_match = by_number.get(source)
        if source_match:
            leaves.extend(_leaf_match_numbers(source_match, by_number))
    return leaves


def _source_match_numbers(slot):
    if not slot.startswith('W') and not slot.startswith('L'):
        return []
    try:
        return [int(slot[1:])]
    except ValueError:
        return []


def projected_bracket_by_match_number(tournament, user):
    return {
        match['match']: match for match in projected_bracket(tournament, user)
    }


def projected_bracket_share_text(tournament, user):
    rounds = projected_bracket_rounds(tournament, user)
    if not rounds:
        return ''

    visible_rounds = [
        group for group in rounds if group['round'] != 'Bronze final'
    ]
    return '#elEga\n%s\nel-e.ga' % _share_bracket_grid(visible_rounds)


def _share_bracket_grid(rounds):
    if not rounds:
        return ''

    leaf_count = len(rounds[0]['matches']) * 2
    row_count = leaf_count * 2 - 1
    rows = [{} for _ in range(row_count)]

    for match_index, match in enumerate(rounds[0]['matches']):
        rows[match_index * 4][0] = _flag(match['home'])
        rows[match_index * 4 + 2][0] = _flag(match['away'])

    for round_index, group in enumerate(rounds):
        row_gap = 2 ** (round_index + 2)
        row_offset = (2 ** (round_index + 1)) - 1
        for match_index, match in enumerate(group['matches']):
            row_index = row_offset + match_index * row_gap
            if row_index < row_count:
                _mark_connector(rows, row_index, round_index)
                rows[row_index][round_index + 1] = _flag(match['winner'])

    return '\n'.join(_render_share_row(row) for row in rows)


def _mark_connector(rows, winner_row, round_index):
    source_row = winner_row - (2**round_index)
    if source_row < 0:
        return
    flag = rows[source_row].get(round_index)
    if flag:
        rows[source_row][round_index] = '%s \\' % flag


def _render_share_row(row):
    if not row:
        return ''
    col_width = 5
    last_col = max(row)
    return ''.join(
        row.get(index, '').ljust(col_width) for index in range(last_col + 1)
    ).rstrip()


def _match_flags(match):
    return '%s/%s' % (_flag(match['home']), _flag(match['away']))


def _projected_champion(rounds):
    final = next(
        (
            match
            for group in rounds
            for match in group['matches']
            if group['round'] == 'Final'
        ),
        None,
    )
    if final is None or final['winner'] is None:
        return None
    return _flag(final['winner'])


def _flag(team):
    if _is_team(team) and team.emoji:
        return team.emoji
    return '?'


def match_number(match):
    number = MATCH_NUMBER_RE.search(match.description or '')
    if number:
        return int(number.group(1))
    return None


def _predictions_by_match_number(tournament, user):
    predictions = (
        user.prediction_set.filter(match__tournament=tournament)
        .select_related('match')
    )
    result = {}
    for prediction in predictions:
        number = match_number(prediction.match)
        if number is not None:
            result[number] = prediction
    return result


def _third_place_candidates(third_places, teams):
    return [
        {
            'zone': row['zone'],
            'team': teams.get(row['team_id'], row['label']),
        }
        for row in third_places[:8]
    ]


def _resolve_slot(
    slot, standings, teams, third_candidates, used_third_zones, winners, losers
):
    if slot.startswith('W') or slot.startswith('L'):
        source = winners if slot.startswith('W') else losers
        try:
            return source.get(int(slot[1:])) or slot
        except ValueError:
            return slot

    if slot.startswith('3'):
        zones = slot[1:].split('/')
        for candidate in third_candidates:
            zone = candidate['zone']
            if zone in zones and zone not in used_third_zones:
                used_third_zones.add(zone)
                return candidate['team']
        return slot

    team_id = standings.get(slot)
    if team_id is None:
        return slot
    return teams.get(team_id, slot)


def _predicted_result(home, away, prediction):
    if not prediction or not _is_team(home) or not _is_team(away):
        return None, None
    if prediction.home_goals is None or prediction.away_goals is None:
        return None, None
    if prediction.home_goals > prediction.away_goals:
        return home, away
    if prediction.home_goals < prediction.away_goals:
        return away, home
    if prediction.penalties == 'L':
        return home, away
    if prediction.penalties == 'V':
        return away, home
    return None, None


def _is_team(value):
    return hasattr(value, 'id') and hasattr(value, 'name')


def _format_team(team):
    if _is_team(team):
        emoji = '%s ' % team.emoji if team.emoji else ''
        return '%s%s' % (emoji, team.code or team.name)
    return str(team)


def _format_score(match):
    home_goals = match['home_goals']
    away_goals = match['away_goals']
    if home_goals is None or away_goals is None:
        return ''
    penalties = ' (P)' if match['penalties'] else ''
    return '%s-%s%s' % (home_goals, away_goals, penalties)
