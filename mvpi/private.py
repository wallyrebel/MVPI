"""Verified Mississippi private volleyball programs outside MHSAA."""

import json
from pathlib import Path
from urllib.parse import urlparse

from .live import Team

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data/volleyball/private-schools.json"


def load_private_teams(season: int) -> tuple[list[Team], dict[str, str], dict[str, str]]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if registry["season"] != season:
        raise ValueError(f"Private school membership needs review for {season}")
    teams, urls = [], {}
    for row in registry["teams"]:
        parsed = urlparse(row["team_url"])
        if parsed.hostname != "www.maxpreps.com" or not parsed.path.startswith("/ms/"):
            raise ValueError(f"Expected a Mississippi MaxPreps school: {row['name']}")
        if row["team_id"] in urls or row["association"] not in {"MAIS", "TSSAA"}:
            raise ValueError(f"Invalid private school entry: {row['name']}")
        teams.append(Team(row["team_id"], row["name"], "Private", "", row["association"]))
        urls[row["team_id"]] = row["team_url"]
    return teams, urls, registry["sources"]


def include_private_teams(teams: list[Team], private_teams: list[Team]) -> list[Team]:
    if {team.team_id for team in teams} & {team.team_id for team in private_teams}:
        raise ValueError("A private registry school is also classified by MHSAA; review membership")
    return teams + private_teams
