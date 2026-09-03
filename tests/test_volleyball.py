from datetime import datetime, timezone

from mvpi.live import Team
from mvpi.maxpreps import MediaRanking, _name_key, _parse_rankings, merge_matches, parse_schedule, reconcile_rankings
from mvpi.volleyball import Match, match_result_value, set_margin


def test_five_set_loss_is_more_competitive_than_sweep_loss():
    close_loss = Match("close", "alpha", "beta", 2, 3, 108, 112)
    sweep_loss = Match("sweep", "alpha", "gamma", 0, 3, 48, 75)
    assert match_result_value(close_loss, "alpha") == 0.0
    assert set_margin(close_loss, "alpha") > set_margin(sweep_loss, "alpha")


def test_five_set_win_is_less_dominant_than_sweep():
    sweep = Match("sweep", "alpha", "beta", 3, 0, 75, 48)
    five_set = Match("five", "alpha", "gamma", 3, 2, 112, 108)
    assert set_margin(sweep, "alpha") > set_margin(five_set, "alpha")


def test_neutral_site_does_not_change_perspective():
    match = Match("neutral", "alpha", "beta", 3, 1, neutral_site=True)
    assert match.perspective("beta")[1:3] == (1, 3)


def test_media_ranking_parser_keeps_record_rank_rating_and_strength():
    html = """
    <table><tr>
      <td class="rank">11</td>
      <td class="team"><a href="/ms/olive-branch/lewisburg-patriots/volleyball/">Lewisburg</a></td>
      <td class="overall">16-5-0</td><td class="rating">17.12</td><td class="strength">10.6</td>
    </tr></table>
    """
    row = _parse_rankings(html)[0]
    assert (row.state_rank, row.record, row.rating, row.strength) == (11, "16-5-0", 17.12, 10.6)


def test_common_mhsaa_and_media_name_variants_normalize_together():
    pairs = [
        ("Diberville Senior High Sch", "D'Iberville"),
        ("Canton Public High School", "Canton"),
        ("Picayune Memorial High School", "Picayune"),
        ("Poplarville Jr Sr High School", "Poplarville"),
        ("Forrest County Agricultural Hi Sch", "Forrest County Agricultural"),
        ("Coahoma County Jr/Sr High School", "Coahoma County"),
        ("Winona Secondary School", "Winona"),
        ("Jefferson Co High", "Jefferson County"),
        ("Northside High School", "North Side"),
        ("Ashland Middle-High School", "Ashland"),
        ("Tupelo Christian", "Tupelo Christian Prep"),
    ]
    assert all(_name_key(official) == _name_key(media) for official, media in pairs)


def test_reconciliation_maps_tcps_but_not_similarly_named_non_mhsaa_team():
    tcps = Team("tupelo-christian", "Tupelo Christian", "1A", "3")
    rankings = [
        MediaRanking(72, "Tupelo Christian Prep", "9-7-0", 5.58, 7.1, "https://www.maxpreps.com/ms/belden/tupelo-christian-prep-eagles/volleyball/"),
        MediaRanking(236, "Tupelo Christian Academy", "0-3-0", -17.81, -6.9, "https://www.maxpreps.com/ms/tupelo/tupelo-christian-academy-crusaders/volleyball/"),
    ]
    matched, unresolved = reconcile_rankings([tcps], rankings)
    assert matched[tcps.team_id].team_name == "Tupelo Christian Prep"
    assert unresolved == ["Tupelo Christian Academy"]


def test_verified_media_aliases_map_to_their_mhsaa_programs():
    teams = [
        Team("thomas-e-edwards", "Thomas E. Edwards", "3A", "3"),
        Team("st-andrew-s", "St. Andrew’s", "3A", "5"),
        Team("franklin", "Franklin High School", "3A", "7"),
        Team("m-s-palmer", "M. S. Palmer High School", "2A", "3"),
        Team("h-w-byers-high-school-5-12", "H. W. Byers High School (5-12)", "1A", "2"),
        Team("resurrection", "Resurrection", "1A", "8"),
    ]
    media_names = ["Edwards", "St. Andrew's Episcopal", "Franklin County", "Palmer", "Byers", "Resurrection Catholic"]
    rankings = [
        MediaRanking(index, name, "3-1-0", 1.0, 1.0, f"https://example.com/{index}")
        for index, name in enumerate(media_names, 1)
    ]
    matched, unresolved = reconcile_rankings(teams, rankings)
    assert set(matched) == {team.team_id for team in teams}
    assert unresolved == []


def test_media_schedule_parser_reads_volleyball_set_score():
    lewisburg = Team("lewisburg", "Lewisburg High School", "7A", "1")
    oxford = Team("oxford", "Oxford High School", "7A", "2")
    source_url = "https://www.maxpreps.com/ms/olive-branch/lewisburg-patriots/volleyball/"
    oxford_url = "https://www.maxpreps.com/ms/oxford/oxford-chargers/volleyball/"
    html = f"""
    <script type="application/ld+json">{{
      "@type":"SportsEvent",
      "url":"https://www.maxpreps.com/ms/volleyball/match/test/?c=abc",
      "startDate":"2026-08-04T23:00:00+00:00",
      "homeTeam":{{"name":"Oxford High School","url":"{oxford_url}"}},
      "awayTeam":{{"name":"Lewisburg High School","url":"{source_url}"}},
      "description":"The Lewisburg varsity volleyball team won their away match against Oxford by a score of 3-2."
    }}</script>
    """
    matches = parse_schedule(
        html,
        source_team=lewisburg,
        source_url=source_url,
        official_by_name={"lewisburg": lewisburg, "oxford": oxford},
        official_by_url={
            "/ms/olive-branch/lewisburg-patriots/volleyball": lewisburg,
            "/ms/oxford/oxford-chargers/volleyball": oxford,
        },
    )
    assert len(matches) == 1
    assert matches[0].perspective("lewisburg")[1:3] == (3, 2)


def test_media_result_wins_conflict_with_mhsaa_fallback():
    played = datetime(2026, 8, 4, 23, tzinfo=timezone.utc)
    media = Match("media:abc", "oxford", "lewisburg", 2, 3, played_at=played, source="media_schedule")
    fallback = Match("mhsaa:abc", "oxford", "lewisburg", 3, 0, played_at=played)
    assert merge_matches([media], [fallback], {"lewisburg", "oxford"}) == [media]


def test_mhsaa_fallback_cannot_expand_authoritative_team_record():
    played = datetime(2026, 8, 12, 0, tzinfo=timezone.utc)
    fallback = Match("mhsaa:other", "lewisburg", "unlisted", 3, 0, played_at=played)
    assert merge_matches([], [fallback], {"lewisburg"}) == []
