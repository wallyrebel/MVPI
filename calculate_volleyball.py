from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
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
from mvpi.private import load_private_teams, include_private_teams
from mvpi.volleyball import match_result_value
from mvpi.external import fetch_external_ratings


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


def current_season_matches(matches, today: date):
    """Exclude stale-season and future results, including cache fallbacks."""
    season_start = date(today.year, 7, 1)
    return [match for match in matches if match.played_at
            and season_start <= match.played_at.astimezone(ZoneInfo("America/Chicago")).date() <= today]


def _schedule_payload(matches, teams, external_names, external, today: date):
    """Per-match rows so each team page can publish its own season schedule.

    Matches are stored once, keyed by team id on both sides, rather than
    duplicated per team. `labels` names every id a match can reference,
    including out-of-state opponents that never appear in the rankings.
    """
    central = ZoneInfo("America/Chicago")
    labels = {team.team_id: team.name for team in teams}
    for team_id, name in external_names.items():
        labels.setdefault(team_id, name)
    for team_id, row in external.items():
        labels.setdefault(team_id, row.get("team") or team_id)

    rows = []
    for match in matches:
        played = match.played_at.astimezone(central).date() if match.played_at else None
        row = {
            "date": played.isoformat() if played else None,
            "home": match.home_team_id,
            "away": match.away_team_id,
            "home_sets": match.home_sets,
            "away_sets": match.away_sets,
        }
        if match.tournament:
            row["tournament"] = True
        if match.neutral_site:
            row["neutral"] = True
        rows.append(row)
    rows.sort(key=lambda row: (row["date"] or "", row["home"], row["away"]))

    referenced = {row["home"] for row in rows} | {row["away"] for row in rows}
    return {
        "metadata": {
            "generated_at": today.isoformat(),
            "matches": len(rows),
            "teams_referenced": len(referenced),
        },
        "labels": {team_id: labels.get(team_id, team_id) for team_id in sorted(referenced)},
        "matches": rows,
    }


def main() -> None:
    today = date.today()
    official_teams = fetch_teams()
    media_fetch = fetch_rankings(Path("data/cache/volleyball-rankings.json"))
    classified_fetch = fetch_classified_teams(Path("data/cache/volleyball-classes.json"))
    teams, unverified_class_teams = build_team_inventory(official_teams, classified_fetch.teams)
    private_teams, private_urls, private_sources = load_private_teams(today.year)
    teams = include_private_teams(teams, private_teams)
    media_signals, unmatched_media = reconcile_rankings(teams, media_fetch.rankings)
    missing_media = [team.name for team in teams if team.team_id not in media_signals]
    media_matches, failed_schedules = fetch_schedules(
        teams,
        media_signals,
        Path("data/cache/volleyball-schedules"),
        team_urls=private_urls,
    )
    # An unranked school's default page can still expose last season's scores.
    # Apply this boundary to both fresh and cached schedule observations.
    media_matches = current_season_matches(media_matches, today)
    media_signals = _advance_media_records(media_signals, media_matches, media_fetch.source_updated_at)
    official_matches, names = fetch_matches(date(today.year, 7, 27), today)
    # MaxPreps is authoritative for volleyball. MHSAA score-center results only
    # fill a contest that the public MaxPreps schedules do not contain.
    matches = merge_matches(media_matches, official_matches, set(media_signals))
    external = fetch_external_ratings(matches, {team.team_id for team in teams},
                                      Path("data/cache/volleyball-external-ratings.json"), today)
    calibration = {}
    rankings = rank(teams, matches, names, media_signals,
                    {key: row["rating"] for key, row in external.items() if row["rating"] is not None}, calibration)
    output = Path("data/volleyball/current.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "metadata": {
            "generated_at": today.isoformat(),
            "formula_version": "MVPI-0.3",
            "external_opponents": len(external),
            "external_opponents_rated": sum(row["rating"] is not None for row in external.values()),
            "external_opponents_unavailable": [row["team"] for row in external.values() if row["rating"] is None],
            "external_rating_calibration": calibration,
            "teams": len(teams),
            "ranked_teams": len(rankings),
            "private_teams": len(private_teams),
            "private_ranked_teams": sum(row.classification == "Private" for row in rankings),
            "private_school_sources": private_sources,
            "unranked_private_teams": [team.name for team in private_teams if team.team_id not in {row.team_id for row in rankings}],
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
        "external_opponents": external,
    }, indent=2) + "\n", encoding="utf-8")
    schedule_output = Path("data/volleyball/matches.json")
    schedule_output.write_text(json.dumps(
        _schedule_payload(matches, teams, names, external, today), indent=2) + "\n", encoding="utf-8")
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
        "schedule_output": str(schedule_output),
        "lewisburg": lewisburg.to_dict() if lewisburg else None,
        "top_five": [row.team for row in rankings[:5]],
    }, indent=2))


if __name__ == "__main__":
    main()
