"""Public MHSAA volleyball teams and match results."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen

from .volleyball import Match

CLASSIFICATIONS_URL = "https://www.misshsaa.com/2024/11/19/2025-27-volleyball-regions/"
SCORE_API_URL = "https://api.scorebooklive.com/v2/graphql"


@dataclass(frozen=True)
class Team:
    team_id: str
    name: str
    classification: str
    region: str
    association: str = "MHSAA"


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None


def _slug(value: str) -> str:
    import re
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    for suffix in ("-high-school", "-senior-high-sch", "-attendance-center"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
    return normalized


def fetch_teams() -> list[Team]:
    request = Request(CLASSIFICATIONS_URL, headers={"User-Agent": "MVPI/0.1"})
    with urlopen(request, timeout=45) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = _TableParser()
    parser.feed(html)
    teams: list[Team] = []
    for row in parser.rows:
        if len(row) < 3 or not row[1].isdigit() or not row[2].isdigit():
            continue
        class_number = int(row[1])
        if class_number not in range(1, 8):
            continue
        teams.append(Team(_slug(row[0]), row[0].title(), f"{class_number}A", row[2]))
    if len(teams) < 120:
        raise ValueError(f"Official volleyball classification parse returned only {len(teams)} teams")
    return teams


_QUERY = """
query MVPIMatches($date: ISO8601Date!, $genderSport: [GenderSportEnum!]!, $level: [LevelEnum!]!, $after: String) {
  contests(date: $date, genderSport: $genderSport, level: $level, orderBy: SCOREBOARD, withoutPlaceholderTeams: true, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id date status contestTypeLabel
      contestParticipants {
        location result score
        participant { __typename ... on Team { id name locationText } }
      }
    }
  }
}
"""


def _fetch_day(day: date) -> list[dict]:
    nodes: list[dict] = []
    after: str | None = None
    while True:
        body = json.dumps({
            "query": _QUERY,
            "variables": {"date": day.isoformat(), "genderSport": ["GIRLS_VOLLEYBALL"], "level": ["VARSITY"], "after": after},
        }).encode()
        request = Request(SCORE_API_URL, data=body, headers={"Content-Type": "application/json", "x-client-policy": "ms-mhsaa", "User-Agent": "MVPI/0.1"})
        with urlopen(request, timeout=45) as response:
            payload = json.loads(response.read())
        contests = payload.get("data", {}).get("contests") or {}
        nodes.extend(contests.get("nodes") or [])
        page = contests.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            return nodes
        after = page.get("endCursor")


def fetch_matches(start: date, end: date, delay: float = 0.04) -> tuple[list[Match], dict[str, str]]:
    matches: list[Match] = []
    names: dict[str, str] = {}
    day = start
    from datetime import timedelta
    while day <= end:
        for node in _fetch_day(day):
            participants = node.get("contestParticipants") or []
            if len(participants) != 2:
                continue
            sides = {str(item.get("location") or "").upper(): item for item in participants}
            if "HOME" not in sides or "AWAY" not in sides:
                continue
            home, away = sides["HOME"], sides["AWAY"]
            home_team, away_team = home.get("participant") or {}, away.get("participant") or {}
            home_name, away_name = str(home_team.get("name") or "").strip(), str(away_team.get("name") or "").strip()
            if not home_name or not away_name:
                continue
            home_id, away_id = _slug(home_name), _slug(away_name)
            names[home_id], names[away_id] = home_name, away_name
            if node.get("status") != "COMPLETED" or home.get("score") is None or away.get("score") is None:
                continue
            matches.append(Match(
                match_id=str(node["id"]), home_team_id=home_id, away_team_id=away_id,
                home_sets=int(home["score"]), away_sets=int(away["score"]),
                tournament="tournament" in str(node.get("contestTypeLabel") or "").lower(),
                played_at=datetime.fromisoformat(str(node["date"]).replace("Z", "+00:00")),
            ))
        day += timedelta(days=1)
        time.sleep(delay)
    return matches, names
