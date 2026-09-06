"""Current-season MaxPreps computer ratings for out-of-state opponents."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
from urllib.parse import urlparse

from .maxpreps import _next_data, _request, _url_key


def parse_external_rating(html: str, team_url: str, season: int, today: date) -> dict:
    data = _next_data(html).get("rankingsData") or {}
    notes = data.get("notes") or []
    updated = next((note.split(":", 1)[1].strip() for note in notes if note.startswith("Last update:")), None)
    if not updated:
        raise ValueError("No rating update date")
    source_day = datetime.strptime(updated, "%m/%d/%Y").date()
    if not 0 <= (today - source_day).days <= 14:
        raise ValueError("Rating is stale or future-dated")
    expected_year = f"{season % 100:02d}-{(season + 1) % 100:02d}"
    rows = [entry for context in data.get("contexts", []) for entry in context.get("entries", [])
            if _url_key(entry.get("teamCanonicalUrl", "")) == _url_key(team_url)
            and entry.get("year") == expected_year]
    if not rows or any(type(row.get("rating")) not in (int, float) or not math.isfinite(row["rating"]) for row in rows):
        raise ValueError("No current-season computer rating for this exact school")
    if len({row["rating"] for row in rows}) != 1:
        raise ValueError("Conflicting computer ratings")
    row = rows[0]
    return {"team": row["schoolName"], "state": row["schoolState"], "rating": row["rating"],
            "season": season, "source_updated_at": source_day.isoformat(),
            "source_url": team_url.rstrip("/") + "/rankings/"}


def fetch_external_ratings(matches, ranked_ids: set[str], cache_path: Path, today: date) -> dict[str, dict]:
    opponents = {}
    for match in matches:
        for team_id, url in [(match.home_team_id, match.home_team_url), (match.away_team_id, match.away_team_url)]:
            parsed = urlparse(url)
            parts = parsed.path.strip("/").split("/")
            if team_id not in ranked_ids and parsed.hostname == "www.maxpreps.com" and len(parts) == 4 and len(parts[0]) == 2 and parts[0] != "ms" and parts[-1] == "volleyball":
                opponents[team_id] = url
    cached = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    def fetch_one(item):
        team_id, url = item
        try:
            row = parse_external_rating(_request(url.rstrip("/") + "/rankings/"), url, today.year, today)
            row.update(status="fresh", retrieved_at=datetime.now(timezone.utc).isoformat())
        except Exception as error:
            row = cached.get(team_id, {})
            valid = (row.get("season") == today.year and row.get("rating") is not None
                     and row.get("source_url") == url.rstrip("/") + "/rankings/"
                     and 0 <= (today - date.fromisoformat(row["source_updated_at"])).days <= 14)
            if valid:
                row = {**row, "status": "cached", "reason": str(error)}
            else:
                row = {"team": urlparse(url).path.split("/")[-3], "state": urlparse(url).path.split("/")[1].upper(),
                       "rating": None, "season": today.year, "source_url": url.rstrip("/") + "/rankings/",
                       "status": "unavailable", "reason": str(error)}
        return team_id, row

    with ThreadPoolExecutor(max_workers=6) as executor:
        result = dict(executor.map(fetch_one, sorted(opponents.items())))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
