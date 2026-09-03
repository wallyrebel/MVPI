from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from mvpi.live import CLASSIFICATIONS_URL, SCORE_API_URL, fetch_matches, fetch_teams
from mvpi.maxpreps import (
    RANKINGS_URL,
    build_team_inventory,
    fetch_classified_teams,
    fetch_rankings,
    fetch_schedules,
    merge_matches,
    reconcile_rankings,
)
from mvpi.ranking import rank
from mvpi.volleyball import match_result_value


def _advance_media_records(media_signals, media_matches, source_updated_at: str | None):
    """Add newer schedule results to the last statewide ranking snapshot."""
    if not source_updated_at:
        return media_signals
    try:
        month, day, year = (int(part) for part in source_updated_at.split("/"))
        snapshot_day = date(year, month, day)
    except (TypeError, ValueError):
        return media_signals
    central = ZoneInfo("America/Chicago")
    newer_by_team = {team_id: [] for team_id in media_signals}
    for match in media_matches:
        # The statewide snapshot is generated early in the morning. Results on
        # that calendar date occur after it and must also roll the record ahead.
        if not match.played_at or match.played_at.astimezone(central).date() < snapshot_day:
            continue
        if match.home_team_id in newer_by_team:
            newer_by_team[match.home_team_id].append(match)
        if match.away_team_id in newer_by_team:
            newer_by_team[match.away_team_id].append(match)
    advanced = {}
    for team_id, signal in media_signals.items():
        parts = signal.record.split("-")
        if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
            advanced[team_id] = signal
            continue
        wins, losses = int(parts[0]), int(parts[1])
        for match in newer_by_team[team_id]:
            if match_result_value(match, team_id) == 1:
                wins += 1
            else:
                losses += 1
        advanced[team_id] = replace(signal, record=f"{wins}-{losses}-0")
    return advanced


def main() -> None:
    today = date.today()
    official_teams = fetch_teams()
    media_fetch = fetch_rankings(Path("data/cache/volleyball-rankings.json"))
    classified_fetch = fetch_classified_teams(Path("data/cache/volleyball-classes.json"))
    teams, unverified_class_teams = build_team_inventory(official_teams, classified_fetch.teams)
    media_signals, unmatched_media = reconcile_rankings(teams, media_fetch.rankings)
    missing_media = [team.name for team in teams if team.team_id not in media_signals]
    media_matches, failed_schedules = fetch_schedules(
        teams,
        media_signals,
        Path("data/cache/volleyball-schedules"),
    )
    media_signals = _advance_media_records(media_signals, media_matches, media_fetch.source_updated_at)
    official_matches, names = fetch_matches(date(today.year, 7, 27), today)
    # MaxPreps is authoritative for volleyball. MHSAA score-center results only
    # fill a contest that the public MaxPreps schedules do not contain.
    matches = merge_matches(media_matches, official_matches, set(media_signals))
    rankings = rank(teams, matches, names, media_signals)
    output = Path("data/volleyball/current.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "metadata": {
            "generated_at": today.isoformat(),
            "teams": len(teams),
            "ranked_teams": len(rankings),
            "completed_matches": len(matches),
            "media_schedule_matches": len(media_matches),
            "media_ranked_teams": len(media_signals),
            "class_feed_teams": len(classified_fetch.teams),
            "unverified_class_feed_teams": len(unverified_class_teams),
            "failed_schedules": failed_schedules,
            "unmatched_media_teams": len(unmatched_media),
            "missing_media_teams": len(missing_media),
            "classification_source": CLASSIFICATIONS_URL,
            "team_discovery_source": RANKINGS_URL.format(page=1),
            "ranking_source": RANKINGS_URL.format(page=1),
            "fallback_score_source": SCORE_API_URL,
            "ranking_source_updated_at": media_fetch.source_updated_at,
            "status": "LIVE",
        },
        "rankings": [row.to_dict() for row in rankings],
    }, indent=2) + "\n", encoding="utf-8")
    lewisburg = next((row for row in rankings if row.team_id == "lewisburg"), None)
    print(json.dumps({
        "teams": len(teams),
        "media_ranked_teams": len(media_signals),
        "class_feed_teams": len(classified_fetch.teams),
        "unverified_class_feed_teams": unverified_class_teams,
        "media_schedule_matches": len(media_matches),
        "completed_matches": len(matches),
        "failed_schedules": failed_schedules,
        "missing_media_teams": missing_media,
        "unmatched_media_teams": unmatched_media,
        "output": str(output),
        "lewisburg": lewisburg.to_dict() if lewisburg else None,
        "top_five": [row.team for row in rankings[:5]],
    }, indent=2))


if __name__ == "__main__":
    main()
