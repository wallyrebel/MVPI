"""Bounded reuse of a verified official classification response, never scores."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .live import CLASSIFICATIONS_URL, Team, _classification_rows, _validate_classifications, fetch_teams

CACHE_PATH = Path("data/volleyball/official-classifications.json")
MAX_AGE = timedelta(days=7)
CYCLE = "2025-27"
CYCLE_START = datetime(2025, 7, 1, tzinfo=timezone.utc)
CYCLE_END = datetime(2027, 7, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class ClassificationFetch:
    teams: list[Team]
    audit: dict


def _validate_capture(payload: dict, now: datetime) -> tuple[list[Team], dict]:
    source = payload["response"]
    html = payload["html"]
    captured = datetime.fromisoformat(source["retrieved_at"])
    if payload["schema_version"] != 1 or payload["cycle"] != CYCLE:
        raise ValueError("Classification cache schema or cycle mismatch")
    if captured.tzinfo is None:
        raise ValueError("Classification cache retrieval time lacks a timezone")
    if not CYCLE_START <= now < CYCLE_END or not CYCLE_START <= captured < CYCLE_END:
        raise ValueError("Classification cache is outside its classification cycle")
    if not timedelta(0) <= now - captured <= MAX_AGE:
        raise ValueError("Classification cache is expired or future-dated")
    if (source["requested_url"] != CLASSIFICATIONS_URL or source["final_url"] != CLASSIFICATIONS_URL
            or source["http_status"] != 200 or "error" in source or "failure_kind" in source
            or source["content_type"].split(";", 1)[0].lower().strip()
            not in {"text/html", "application/xhtml+xml"}):
        raise ValueError("Classification cache lacks successful official article provenance")
    raw = html.encode("utf-8")
    if len(raw) != source["body_bytes"] or hashlib.sha256(raw).hexdigest() != source["body_sha256"]:
        raise ValueError("Classification cache checksum mismatch")
    if f"{CYCLE} Volleyball Regions" not in html:
        raise ValueError("Classification cache article cycle mismatch")
    teams, rows = _classification_rows(html)
    _validate_classifications(teams)
    if (source["parsed_teams"] != len(teams) or source["table_rows"] != rows
            or source["classes"] != sorted({team.classification for team in teams})):
        raise ValueError("Classification cache inventory disagrees with capture metadata")
    return teams, {"source_url": CLASSIFICATIONS_URL, "cycle": CYCLE,
                   "retrieved_at": captured.isoformat(),
                   "expires_at": min(captured + MAX_AGE, CYCLE_END).isoformat(),
                   "body_sha256": source["body_sha256"], "teams": len(teams)}


def fetch_classifications(cache_path: Path = CACHE_PATH,
                          diagnostics_dir: Path = Path("work/classifications")) -> ClassificationFetch:
    """Try the official source, then reuse a recent verified capture for outages.

    Incomplete/changed responses, redirects, content-type changes, permanent HTTP
    errors and any response with school rows fail closed. The strict fetch keeps
    its existing retry policy and never attempts to solve or bypass a challenge.
    """
    used_cache = False
    try:
        fetch_teams(diagnostics_dir)
    except ValueError as source_error:
        response = json.loads((diagnostics_dir / "response.json").read_text(encoding="utf-8"))
        attempts = response["attempts"]
        eligible = all(
            not row.get("parsed_teams", 0) and (
                row["failure_kind"] in {"upstream_challenge", "transport_error"}
                or row["failure_kind"] == "http_error"
                and (row["http_status"] in {408, 429} or 500 <= row["http_status"] < 600)
            ) for row in attempts
        )
        if not attempts or not eligible:
            raise
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            teams, audit = _validate_capture(payload, datetime.now(timezone.utc))
        except (ValueError, OSError, KeyError, TypeError, AttributeError) as cache_error:
            raise ValueError(f"{source_error}; classification cache rejected: {cache_error}") from source_error
        used_cache = True
    else:
        response = json.loads((diagnostics_dir / "response.json").read_text(encoding="utf-8"))
        source = response["attempts"][-1]
        payload = {"schema_version": 1, "cycle": CYCLE, "response": source,
                   "html": (diagnostics_dir / f"attempt-{source['attempt']}.html").read_bytes().decode("utf-8")}
        teams, audit = _validate_capture(payload, datetime.now(timezone.utc))
        # Publish only a fully validated capture, atomically. A failed read never
        # overwrites the last success or advances its original retrieval time.
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(cache_path)
    audit.update(used_cache=used_cache, checked_at=datetime.now(timezone.utc).isoformat(),
                 fallback_reason=response["attempts"][-1].get("failure_kind") if used_cache else None,
                 live_attempts=response["attempts"])
    response["classification_fetch"] = audit
    (diagnostics_dir / "response.json").write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
    print("Official classification selection: " + json.dumps(audit), flush=True)
    return ClassificationFetch(teams, audit)
