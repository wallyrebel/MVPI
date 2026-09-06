"""Volleyball-specific primitives for the Mississippi Volleyball Power Index."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import tanh


@dataclass(frozen=True)
class Match:
    match_id: str
    home_team_id: str
    away_team_id: str
    home_sets: int
    away_sets: int
    home_points: int | None = None
    away_points: int | None = None
    neutral_site: bool = False
    tournament: bool = False
    played_at: datetime | None = None
    status: str = "COMPLETED"
    source: str = "mhsaa_score_center"
    home_team_url: str = ""
    away_team_url: str = ""

    @property
    def completed(self) -> bool:
        return self.status == "COMPLETED" and self.home_sets >= 0 and self.away_sets >= 0 and self.home_sets != self.away_sets

    def perspective(self, team_id: str) -> tuple[str, int, int, int | None, int | None]:
        if team_id == self.home_team_id:
            return self.away_team_id, self.home_sets, self.away_sets, self.home_points, self.away_points
        if team_id == self.away_team_id:
            return self.home_team_id, self.away_sets, self.home_sets, self.away_points, self.home_points
        raise ValueError(f"Team {team_id!r} did not play match {self.match_id!r}")


def set_margin(match: Match, team_id: str) -> float:
    """Convert a match result into a bounded performance margin."""
    _, sets_for, sets_against, points_for, points_against = match.perspective(team_id)
    margin = 2.0 * tanh((sets_for - sets_against) / 2.0)
    if points_for is not None and points_against is not None:
        margin += 0.75 * tanh((points_for - points_against) / 50.0)
    return margin


def match_result_value(match: Match, team_id: str) -> float:
    _, sets_for, sets_against, _, _ = match.perspective(team_id)
    if sets_for > sets_against:
        return 1.0
    if sets_for == sets_against:
        return 0.5
    return 0.0
