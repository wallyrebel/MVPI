"""Set-aware MVPI ranking engine."""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass

from .live import Team
from .maxpreps import MediaRanking
from .volleyball import Match, match_result_value, set_margin

CLASS_PRIOR = {"7A": 0.9, "6A": 0.6, "5A": 0.3, "4A": 0.0, "3A": -0.3, "2A": -0.6, "1A": -0.9}


@dataclass(frozen=True)
class Ranking:
    rank: int
    team_id: str
    team: str
    classification: str
    region: str
    record: str
    matches: int
    set_matches: int
    sets_for: int
    sets_against: int
    mvpi: float
    sos: float
    opponent_sos: float
    performance: float
    set_percentage: float
    recent: float
    media_rank: int | None
    media_rating: float | None
    association: str = "MHSAA"

    def to_dict(self) -> dict:
        return asdict(self)


def _percentiles(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    if len(ordered) <= 1:
        return {team_id: 50.0 for team_id in values}
    return {team_id: 100.0 * index / (len(ordered) - 1) for index, (team_id, _) in enumerate(ordered)}


def _record(value: str) -> tuple[int, int] | None:
    match = __import__("re").fullmatch(r"\s*(\d+)-(\d+)(?:-\d+)?\s*", value)
    return (int(match.group(1)), int(match.group(2))) if match else None


def rank(
    teams: list[Team],
    matches: list[Match],
    external_names: dict[str, str],
    media: dict[str, MediaRanking] | None = None,
) -> list[Ranking]:
    media = media or {}
    ranked_ids = {team.team_id for team in teams}
    all_ids = ranked_ids | {m.home_team_id for m in matches} | {m.away_team_id for m in matches}
    by_team: dict[str, list[Match]] = defaultdict(list)
    for match in matches:
        if match.completed and ({match.home_team_id, match.away_team_id} & ranked_ids):
            by_team[match.home_team_id].append(match)
            by_team[match.away_team_id].append(match)
    ratings = {team_id: CLASS_PRIOR.get(next((t.classification for t in teams if t.team_id == team_id), ""), 0.0) for team_id in all_ids}
    for _ in range(100):
        updated: dict[str, float] = {}
        for team_id in all_ids:
            contests = by_team.get(team_id, [])
            prior = CLASS_PRIOR.get(next((t.classification for t in teams if t.team_id == team_id), ""), 0.0)
            weight = 1.5 if team_id in ranked_ids and len(contests) <= 4 else 0.35
            values = [ratings.get(match.perspective(team_id)[0], 0.0) + set_margin(match, team_id) for match in contests]
            updated[team_id] = (prior * weight + sum(values)) / (weight + len(values)) if values else prior
        center = statistics.fmean(updated[team_id] for team_id in ranked_ids)
        updated = {team_id: value - center for team_id, value in updated.items()}
        if max(abs(updated[k] - ratings.get(k, 0.0)) for k in updated) < 0.001:
            ratings = updated
            break
        ratings = updated

    # A published statewide row is enough to include a team even when its page
    # has not exposed every individual tournament match.
    eligible = [team for team in teams if by_team.get(team.team_id) or team.team_id in media]
    raw_performance, raw_sos, raw_record, raw_sets, raw_recent = {}, {}, {}, {}, {}
    raw_media_rank: dict[str, float] = {}
    raw_media_sos: dict[str, float] = {}
    stats = {}
    worst_media_rank = max((row.state_rank for row in media.values()), default=len(teams)) + 1
    weakest_media_sos = min((row.strength for row in media.values()), default=0.0) - 1.0
    for team in eligible:
        contests = sorted(by_team.get(team.team_id, []), key=lambda m: m.played_at or m.match_id)
        wins = sum(match_result_value(m, team.team_id) == 1 for m in contests)
        losses = len(contests) - wins
        sf = sum(m.perspective(team.team_id)[1] for m in contests)
        sa = sum(m.perspective(team.team_id)[2] for m in contests)
        opponent_ratings = [ratings.get(m.perspective(team.team_id)[0], 0.0) for m in contests]
        performances = [ratings.get(m.perspective(team.team_id)[0], 0.0) + set_margin(m, team.team_id) for m in contests]
        raw_performance[team.team_id] = ratings.get(team.team_id, 0.0)
        raw_sos[team.team_id] = statistics.fmean(opponent_ratings) if opponent_ratings else 0.0
        published = _record(media[team.team_id].record) if team.team_id in media else None
        published_wins, published_losses = published or (wins, losses)
        published_matches = published_wins + published_losses
        # MaxPreps' statewide snapshot and team schedule occasionally update at
        # different times.  Keep the fuller MaxPreps record without inventing
        # results: the snapshot wins when it covers more matches (tournaments
        # can lack detail), while a longer schedule wins when it is newer.
        if len(contests) > published_matches:
            published_wins, published_losses = wins, losses
            published_matches = len(contests)
        raw_record[team.team_id] = published_wins / published_matches if published_matches else 0.5
        raw_sets[team.team_id] = sf / (sf + sa) if sf + sa else 0.5
        raw_recent[team.team_id] = statistics.fmean(performances[-5:]) if performances else 0.0
        raw_media_rank[team.team_id] = -float(media[team.team_id].state_rank) if team.team_id in media else -float(worst_media_rank)
        raw_media_sos[team.team_id] = media[team.team_id].strength if team.team_id in media else weakest_media_sos
        stats[team.team_id] = (published_wins, published_losses, sf, sa, published_matches, len(contests))
    components = [_percentiles(values) for values in (raw_performance, raw_sos, raw_record, raw_sets, raw_recent, raw_media_rank, raw_media_sos)]
    scores = {
        team.team_id:
        0.35 * components[0][team.team_id]
        + 0.15 * components[1][team.team_id]
        + 0.10 * components[2][team.team_id]
        + 0.10 * components[3][team.team_id]
        + 0.05 * components[4][team.team_id]
        + 0.15 * components[5][team.team_id]
        + 0.10 * components[6][team.team_id]
        for team in eligible
    }
    ordered = sorted(eligible, key=lambda team: (-scores[team.team_id], -raw_performance[team.team_id], team.name))
    rows = []
    for position, team in enumerate(ordered, 1):
        wins, losses, sf, sa, played, set_matches = stats[team.team_id]
        signal = media.get(team.team_id)
        rows.append(
            Ranking(
                position,
                team.team_id,
                signal.team_name if signal else team.name,
                team.classification,
                team.region,
                f"{wins}-{losses}",
                played,
                set_matches,
                sf,
                sa,
                round(scores[team.team_id], 1),
                round(signal.strength, 1) if signal else round(raw_sos[team.team_id], 1),
                round(components[1][team.team_id], 1),
                round(components[0][team.team_id], 1),
                round(components[3][team.team_id], 1),
                round(components[4][team.team_id], 1),
                signal.state_rank if signal else None,
                round(signal.rating, 2) if signal else None,
                team.association,
            )
        )
    return rows
