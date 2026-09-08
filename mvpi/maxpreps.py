"""Statewide ranking, classified team, and schedule data for MVPI.

The seven public 1A-7A ranking feeds discover active team candidates and supply
their current public names.  The MHSAA directory confirms membership, supplies
official region metadata, and keeps not-yet-ranked member schools in inventory.
"""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .live import Team, _slug
from .volleyball import Match

RANKINGS_URL = "https://www.maxpreps.com/ms/volleyball/rankings/{page}/"
RANKINGS_ROOT = "https://www.maxpreps.com"


@dataclass(frozen=True)
class MediaRanking:
    state_rank: int
    team_name: str
    record: str
    rating: float
    strength: float
    team_url: str


@dataclass(frozen=True)
class MediaFetch:
    rankings: list[MediaRanking]
    retrieved_at: datetime
    source_updated_at: str | None
    used_cache: bool = False


@dataclass(frozen=True)
class ClassifiedMediaTeam:
    team_name: str
    team_url: str
    classification: str


@dataclass(frozen=True)
class ClassifiedTeamsFetch:
    teams: list[ClassifiedMediaTeam]
    retrieved_at: datetime
    used_cache: bool = False


class _RankingsParser(HTMLParser):
    fields = {"rank", "team", "overall", "rating", "strength"}

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, str]] = []
        self._row: dict[str, str] | None = None
        self._field: str | None = None
        self._text: list[str] = []
        self._ignored_tag: str | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "tr":
            self._row = {}
        elif tag == "td" and self._row is not None:
            classes = set((values.get("class") or "").split())
            self._field = next((field for field in self.fields if field in classes), None)
            self._text = []
        elif tag == "a" and self._row is not None and self._field == "team" and values.get("href"):
            self._row["team_url"] = values["href"]
        elif (
            tag in {"div", "span"}
            and self._row is not None
            and self._field == "team"
            and "photo-or-initial" in set((values.get("class") or "").split())
        ):
            self._ignored_tag = tag

    def handle_data(self, data: str) -> None:
        if self._field is not None and self._ignored_tag is None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == self._ignored_tag:
            self._ignored_tag = None
            return
        if tag == "td" and self._row is not None and self._field is not None:
            self._row[self._field] = " ".join("".join(self._text).split())
            self._field = None
            self._text = []
        elif tag == "tr" and self._row is not None:
            if self._row.get("rank", "").isdigit() and self._row.get("team"):
                self.rows.append(self._row)
            self._row = None


class _JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.documents: list[str] = []
        self._capturing = False
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "script" and "ld+json" in (values.get("type") or "").lower():
            self._capturing = True
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._capturing:
            self.documents.append("".join(self._text))
            self._capturing = False
            self._text = []


def _request(url: str) -> str:
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "MVPI/0.2 (+weekly Mississippi volleyball rankings)",
        },
    )
    with urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def _parse_rankings(html: str) -> list[MediaRanking]:
    parser = _RankingsParser()
    parser.feed(html)
    rows: list[MediaRanking] = []
    for row in parser.rows:
        rows.append(
            MediaRanking(
                state_rank=int(row["rank"]),
                team_name=row["team"],
                record=row.get("overall", ""),
                rating=float(row["rating"]),
                strength=float(row.get("strength") or 0.0),
                team_url=urljoin(RANKINGS_ROOT, row.get("team_url", "")),
            )
        )
    return rows


def fetch_rankings(cache_path: Path, request_delay: float = 0.08) -> MediaFetch:
    retrieved_at = datetime.now(timezone.utc)
    rankings: list[MediaRanking] = []
    source_updated_at: str | None = None
    try:
        for page in range(1, 21):
            html = _request(RANKINGS_URL.format(page=page))
            page_rows = _parse_rankings(html)
            if page == 1:
                updated = re.search(r"Last updated:(?:<!-- -->)?\s*([^<]+)", html, flags=re.IGNORECASE)
                source_updated_at = updated.group(1).strip() if updated else None
            if not page_rows:
                break
            rankings.extend(page_rows)
            if len(page_rows) < 25:
                break
            time.sleep(request_delay)
        ranks = [row.state_rank for row in rankings]
        if len(rankings) < 180 or len(ranks) != len(set(ranks)):
            raise ValueError(f"Statewide media ranking returned {len(rankings)} usable rows")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "retrieved_at": retrieved_at.isoformat(),
                    "source_updated_at": source_updated_at,
                    "rankings": [asdict(row) for row in rankings],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return MediaFetch(rankings, retrieved_at, source_updated_at)
    except Exception:
        if not cache_path.exists():
            raise
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        return MediaFetch(
            [MediaRanking(**row) for row in payload["rankings"]],
            datetime.fromisoformat(payload["retrieved_at"]),
            payload.get("source_updated_at"),
            True,
        )


def _class_ranking_urls(html: str) -> dict[str, str]:
    """Extract the current-season 1A-7A feeds from the statewide page."""
    urls: dict[str, str] = {}
    pattern = re.compile(
        r'href=["\']([^"\']*/class/class-([1-7])a/rankings/1/[^"\']*)["\']',
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(html):
        classification = f"{match.group(2)}A"
        urls[classification] = urljoin(RANKINGS_ROOT, unescape(match.group(1)))
    return urls


def _ranking_page_url(url: str, page: int) -> str:
    return re.sub(r"/rankings/\d+/", f"/rankings/{page}/", url, count=1)


def fetch_classified_teams(cache_path: Path, request_delay: float = 0.08) -> ClassifiedTeamsFetch:
    """Fetch every team listed in the current 1A-7A ranking feeds."""
    retrieved_at = datetime.now(timezone.utc)
    try:
        statewide_html = _request(RANKINGS_URL.format(page=1))
        class_urls = _class_ranking_urls(statewide_html)
        if set(class_urls) != {f"{number}A" for number in range(1, 8)}:
            raise ValueError(f"Expected seven class ranking feeds, found {sorted(class_urls)}")

        by_url: dict[str, ClassifiedMediaTeam] = {}
        for classification in sorted(class_urls, key=lambda value: int(value[:-1])):
            for page in range(1, 21):
                try:
                    html = _request(_ranking_page_url(class_urls[classification], page))
                except HTTPError as error:
                    # Some class feeds contain exactly 25 teams. Their second
                    # page returns 404 instead of an empty ranking table.
                    if error.code == 404 and page > 1:
                        break
                    raise
                page_rows = _parse_rankings(html)
                if not page_rows:
                    break
                for row in page_rows:
                    key = _url_key(row.team_url)
                    current = by_url.get(key)
                    if current and current.classification != classification:
                        raise ValueError(f"Team appears in multiple classes: {row.team_name}")
                    by_url[key] = ClassifiedMediaTeam(row.team_name, row.team_url, classification)
                if len(page_rows) < 25:
                    break
                time.sleep(request_delay)

        teams = list(by_url.values())
        if len(teams) < 150:
            raise ValueError(f"Class ranking feeds returned only {len(teams)} teams")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "retrieved_at": retrieved_at.isoformat(),
                    "teams": [asdict(team) for team in teams],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return ClassifiedTeamsFetch(teams, retrieved_at)
    except Exception:
        if not cache_path.exists():
            raise
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        return ClassifiedTeamsFetch(
            [ClassifiedMediaTeam(**row) for row in payload["teams"]],
            datetime.fromisoformat(payload["retrieved_at"]),
            True,
        )


def _name_key(name: str) -> str:
    value = re.sub(r"\([^)]*\)", " ", name).casefold().replace("saint", "st")
    # Apostrophes are not word boundaries in school names: D'Iberville and
    # Andrews must compare as diberville and andrews, not as split tokens.
    value = re.sub(r"(?<=[a-z0-9])['’](?=[a-z0-9])", "", value)
    words = re.findall(r"[a-z0-9]+", value)
    ignored = {
        "high", "school", "senior", "attendance", "center", "campus",
        "public", "middle", "jr", "sr", "memorial", "secondary", "hi",
        "sch", "prep",
    }
    normalized = ("county" if word == "co" else word for word in words if word not in ignored)
    # Collapsing whitespace intentionally treats North Side and Northside as
    # the same label while preserving word order for every other school.
    return "".join(normalized)


# Verified MHSAA member names whose media labels omit or add meaningful words.
# These are explicit because globally discarding words such as "county" would
# incorrectly merge distinct programs (for example, Newton and Newton County).
_MEDIA_TEAM_ALIASES = {
    _name_key("Edwards"): "thomas-e-edwards",
    _name_key("St. Andrew's Episcopal"): "st-andrew-s",
    _name_key("Franklin County"): "franklin",
    _name_key("Palmer"): "m-s-palmer",
    _name_key("Byers"): "h-w-byers-high-school-5-12",
    _name_key("Resurrection Catholic"): "resurrection",
    _name_key("Mississippi School for the Deaf"): "miss-school-for-the-deaf",
}


def reconcile_rankings(teams: list[Team], rankings: list[MediaRanking]) -> tuple[dict[str, MediaRanking], list[str]]:
    team_by_id = {team.team_id: team for team in teams}
    by_key: dict[str, list[Team]] = {}
    for team in teams:
        by_key.setdefault(_name_key(team.name), []).append(team)
    matched: dict[str, MediaRanking] = {}
    unresolved: list[str] = []
    for row in rankings:
        alias_id = _MEDIA_TEAM_ALIASES.get(_name_key(row.team_name))
        if alias_id:
            if alias_id in team_by_id and alias_id not in matched:
                matched[alias_id] = row
            else:
                unresolved.append(row.team_name)
            continue
        candidates = by_key.get(_name_key(row.team_name), [])
        if len(candidates) == 1:
            team_id = candidates[0].team_id
            if team_id in matched:
                unresolved.append(row.team_name)
            else:
                matched[team_id] = row
        elif candidates:
            # City in the team URL resolves the rare duplicate school name.
            url_path = urlparse(row.team_url).path.lower()
            selected = next((team for team in candidates if _slug(team.name) in url_path), None)
            if selected:
                matched[selected.team_id] = row
        else:
            unresolved.append(row.team_name)
    return matched, unresolved


def build_team_inventory(
    official_teams: list[Team],
    classified_media_teams: list[ClassifiedMediaTeam],
) -> tuple[list[Team], list[str]]:
    """Merge class-feed discovery with official class and region metadata.

    The class feeds lead discovery and naming. An official member absent from
    those feeds remains available so it is not dropped merely because it has no
    published ranking yet. Class-feed entries not confirmed by the official
    directory are reported for review but excluded; a public 1A-7A label alone
    does not prove MHSAA membership.
    """
    discovery_rows = [
        MediaRanking(index, row.team_name, "", 0.0, 0.0, row.team_url)
        for index, row in enumerate(classified_media_teams, 1)
    ]
    matched, _ = reconcile_rankings(official_teams, discovery_rows)
    official_by_id = {team.team_id: team for team in official_teams}
    official_by_url = {
        _url_key(signal.team_url): official_by_id[team_id]
        for team_id, signal in matched.items()
    }

    inventory: list[Team] = []
    used_ids: set[str] = set()
    media_only: list[str] = []
    for row in classified_media_teams:
        official = official_by_url.get(_url_key(row.team_url))
        if official:
            team = Team(official.team_id, row.team_name, official.classification, official.region, official.association)
        else:
            media_only.append(row.team_name)
            continue
        if team.team_id not in used_ids:
            inventory.append(team)
            used_ids.add(team.team_id)

    for team in official_teams:
        if team.team_id not in used_ids:
            inventory.append(team)
            used_ids.add(team.team_id)
    return inventory, sorted(media_only)


def _events(value: Any):
    if isinstance(value, dict):
        event_type = value.get("@type")
        if event_type == "SportsEvent" or isinstance(event_type, list) and "SportsEvent" in event_type:
            yield value
        for child in value.values():
            yield from _events(child)
    elif isinstance(value, list):
        for child in value:
            yield from _events(child)


def _team_name(value: Any) -> str:
    return str(value.get("name") or "").strip() if isinstance(value, dict) else ""


def _team_url(value: Any) -> str:
    return str(value.get("url") or "").strip() if isinstance(value, dict) else ""


def _url_key(value: str) -> str:
    return urlparse(urljoin(RANKINGS_ROOT, value)).path.rstrip("/").lower()


def _next_data(html: str) -> dict:
    found = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    return json.loads(found.group(1)).get("props", {}).get("pageProps", {}) if found else {}


def _resolve_team(name, url, by_name, by_url):
    key = _url_key(url)
    team = by_url.get(key)
    # A Tennessee school named Oxford must never resolve to Oxford, MS.
    if not team and (not url or key.startswith("/ms/")):
        team = by_name.get(_name_key(name))
    if team:
        return team.team_id
    return "external:" + key if url and not key.startswith("/ms/") else _slug(name)


_SCORE_RE = re.compile(r"\b(won|lost|tied)\b.*?\bby a score of\s+(\d+)-(\d+)", re.IGNORECASE)
_ACTOR_RE = re.compile(r"\bthe (.+?) varsity (?:girls )?volleyball team (won|lost|tied)\b", re.IGNORECASE)


def parse_schedule(
    html: str,
    *,
    source_team: Team,
    source_url: str,
    official_by_name: dict[str, Team],
    official_by_url: dict[str, Team],
) -> list[Match]:
    parser = _JsonLdParser()
    parser.feed(html)
    matches: list[Match] = []
    seen: set[str] = set()
    for document in parser.documents:
        try:
            decoded = json.loads(document)
        except json.JSONDecodeError:
            continue
        for event in _events(decoded):
            event_url = str(event.get("url") or "")
            if not event_url:
                continue
            contest = parse_qs(urlparse(event_url).query).get("c", [event_url])[0]
            if contest in seen:
                continue
            seen.add(contest)
            home, away = event.get("homeTeam"), event.get("awayTeam")
            home_name, away_name = _team_name(home), _team_name(away)
            home_url, away_url = _team_url(home), _team_url(away)
            started = event.get("startDate")
            if not home_name or not away_name or not started:
                continue
            source_key = _url_key(source_url)
            if _url_key(home_url) == source_key or (not home_url and _name_key(home_name) == _name_key(source_team.name)):
                source_side = "home"
            elif _url_key(away_url) == source_key or (not away_url and _name_key(away_name) == _name_key(source_team.name)):
                source_side = "away"
            else:
                continue
            description = str(event.get("description") or "")
            score_match = _SCORE_RE.search(description)
            if not score_match:
                continue
            result, high_text, low_text = score_match.groups()
            high, low = int(high_text), int(low_text)
            actor = _ACTOR_RE.search(description)
            actor_side = source_side
            if actor:
                actor_name = actor.group(1)
                if _name_key(actor_name) == _name_key(home_name):
                    actor_side = "home"
                elif _name_key(actor_name) == _name_key(away_name):
                    actor_side = "away"
            actor_score, other_score = (high, low) if result.lower() != "lost" else (low, high)
            home_sets, away_sets = (actor_score, other_score) if actor_side == "home" else (other_score, actor_score)

            home_id = _resolve_team(home_name, home_url, official_by_name, official_by_url)
            away_id = _resolve_team(away_name, away_url, official_by_name, official_by_url)
            if source_side == "home":
                home_id = source_team.team_id
            else:
                away_id = source_team.team_id
            played_at = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
            matches.append(
                Match(
                    match_id=f"media:{contest}",
                    home_team_id=home_id,
                    away_team_id=away_id,
                    home_sets=home_sets,
                    away_sets=away_sets,
                    tournament="tournament" in description.lower(),
                    played_at=played_at,
                    source="media_schedule",
                    home_team_url=home_url,
                    away_team_url=away_url,
                )
            )
    # MaxPreps omits some tournament contests from JSON-LD. Its schedule's
    # embedded data contains the completed results used by the visible table.
    for row in _next_data(html).get("contests", []):
        if not isinstance(row, list) or len(row) < 30 or row[15] != 4:
            continue
        sides = row[0]
        if not isinstance(sides, list) or len(sides) != 2 or any(len(side) < 17 for side in sides):
            continue
        if {side[5] for side in sides} != {"W", "L"}:
            continue
        if any(type(side[6]) is not int or side[6] not in range(4) for side in sides):
            continue
        winner = next(side for side in sides if side[5] == "W")
        loser = next(side for side in sides if side[5] == "L")
        if winner[6] not in (2, 3) or loser[6] >= winner[6]:
            continue
        if not any(_url_key(side[13]) == _url_key(source_url) for side in sides):
            continue
        match_id = f"media:{row[1]}"
        if any(match.match_id == match_id for match in matches):
            continue
        from zoneinfo import ZoneInfo
        played = datetime.fromisoformat(row[11])
        if played.tzinfo is None:
            played = played.replace(tzinfo=ZoneInfo("America/Chicago"))
        # Side order is immaterial to this neutral, set-based formula.
        a, b = sides
        matches.append(Match(
            match_id, _resolve_team(a[14], a[13], official_by_name, official_by_url),
            _resolve_team(b[14], b[13], official_by_name, official_by_url), a[6], b[6],
            played_at=played, tournament="tournament" in str(row[29]).lower(),
            source="media_schedule", home_team_url=a[13], away_team_url=b[13],
        ))
    return matches


def _schedule_url(team_url: str) -> str:
    path = urlparse(team_url).path.rstrip("/")
    if not path.endswith("/volleyball"):
        raise ValueError(f"Unexpected volleyball team URL: {team_url}")
    return team_url.rstrip("/") + "/schedule/"


def fetch_schedules(
    teams: list[Team],
    signals: dict[str, MediaRanking],
    cache_dir: Path,
    *,
    workers: int = 8,
    team_urls: dict[str, str] | None = None,
) -> tuple[list[Match], list[str]]:
    team_by_id = {team.team_id: team for team in teams}
    official_by_name = {_name_key(team.name): team for team in teams}
    urls = {**(team_urls or {}), **{team_id: row.team_url for team_id, row in signals.items()}}
    official_by_url = {_url_key(url): team_by_id[team_id] for team_id, url in urls.items()}
    failures: list[str] = []

    def fetch_one(team_id: str, team_url: str) -> tuple[str, list[Match]]:
        cache_path = cache_dir / f"{team_id}.json"
        try:
            html = _request(_schedule_url(team_url))
            parsed = parse_schedule(
                html,
                source_team=team_by_id[team_id],
                source_url=team_url,
                official_by_name=official_by_name,
                official_by_url=official_by_url,
            )
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "matches": [
                            {
                                **asdict(match),
                                "played_at": match.played_at.isoformat() if match.played_at else None,
                            }
                            for match in parsed
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            return team_id, parsed
        except Exception:
            if not cache_path.exists():
                raise
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != 2:
                raise ValueError("Schedule cache requires refresh for state-safe opponent IDs")
            return team_id, [
                Match(**{**row, "played_at": datetime.fromisoformat(row["played_at"]) if row.get("played_at") else None})
                for row in payload.get("matches", [])
            ]

    observations: list[Match] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        jobs = {executor.submit(fetch_one, team_id, url): team_id for team_id, url in urls.items()}
        for future in as_completed(jobs):
            team_id = jobs[future]
            try:
                _, rows = future.result()
                observations.extend(rows)
            except Exception:
                failures.append(team_id)

    # A contest appears on both teams' schedules.  Its media contest id is the
    # stable cross-page identity, so keep only one copy.
    unique = {match.match_id: match for match in observations}
    return list(unique.values()), sorted(failures)


def merge_matches(
    primary: list[Match],
    secondary: list[Match],
    authoritative_team_ids: set[str] | None = None,
) -> list[Match]:
    """Prefer complete schedule observations and add non-duplicate MHSAA rows."""
    authoritative_team_ids = authoritative_team_ids or set()
    merged = {match.match_id: match for match in primary}
    primary_dates: dict[tuple[str, str], list] = {}
    for match in primary:
        pair = tuple(sorted((match.home_team_id, match.away_team_id)))
        if match.played_at:
            primary_dates.setdefault(pair, []).append(match.played_at.date())
    for match in secondary:
        # If either participant has a matched MaxPreps team page, MaxPreps owns
        # that team's record and result universe.  Adding a fallback-only game
        # would make its set coverage exceed its authoritative record.
        if {match.home_team_id, match.away_team_id} & authoritative_team_ids:
            continue
        pair = tuple(sorted((match.home_team_id, match.away_team_id)))
        # Dates in the two feeds can straddle midnight UTC.  Once MaxPreps has
        # the same pairing within one calendar day, it owns the contest even if
        # the fallback source disagrees with the score.
        if match.played_at and any(
            abs((match.played_at.date() - primary_day).days) <= 1
            for primary_day in primary_dates.get(pair, [])
        ):
            continue
        merged[match.match_id] = match
    return list(merged.values())
