from datetime import datetime, timezone

from mvpi.live import Team
from mvpi.maxpreps import (
    ClassifiedMediaTeam,
    MediaRanking,
    _class_ranking_urls,
    _name_key,
    _parse_rankings,
    build_team_inventory,
    merge_matches,
    parse_schedule,
    reconcile_rankings,
)
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


def test_class_ranking_urls_are_discovered_from_current_season_navigation():
    html = """
    <a href="/ms/volleyball/26-27/class/class-1a/rankings/1/?id=one&amp;x=1">1A</a>
    <a href="/ms/volleyball/26-27/class/class-7a/rankings/1/?id=seven">7A</a>
    """
    urls = _class_ranking_urls(html)
    assert set(urls) == {"1A", "7A"}
    assert urls["1A"].endswith("?id=one&x=1")


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
        Team("miss-school-for-the-deaf", "Miss. School For The Deaf", "1A", "4"),
    ]
    media_names = ["Edwards", "St. Andrew's Episcopal", "Franklin County", "Palmer", "Byers", "Resurrection Catholic", "Mississippi School for the Deaf"]
    rankings = [
        MediaRanking(index, name, "3-1-0", 1.0, 1.0, f"https://example.com/{index}")
        for index, name in enumerate(media_names, 1)
    ]
    matched, unresolved = reconcile_rankings(teams, rankings)
    assert set(matched) == {team.team_id for team in teams}
    assert unresolved == []


def test_class_feeds_update_official_names_and_preserve_unranked_official_team():
    official = [
        Team("tupelo-christian", "Tupelo Christian", "1A", "3"),
        Team("waiting-for-results", "Waiting For Results", "2A", "4"),
    ]
    classified = [
        ClassifiedMediaTeam(
            "Tupelo Christian Prep",
            "https://www.maxpreps.com/ms/belden/tupelo-christian-prep-eagles/volleyball/",
            "1A",
        ),
        ClassifiedMediaTeam(
            "New Discovery",
            "https://www.maxpreps.com/ms/example/new-discovery/volleyball/",
            "3A",
        ),
    ]
    inventory, unverified = build_team_inventory(official, classified)
    by_id = {team.team_id: team for team in inventory}
    assert by_id["tupelo-christian"].name == "Tupelo Christian Prep"
    assert by_id["tupelo-christian"].region == "3"
    assert "new-discovery" not in by_id
    assert "waiting-for-results" in by_id
    assert unverified == ["New Discovery"]


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


def test_private_registry_includes_mais_and_northpoint_without_mhsaa_reclassification():
    from mvpi.private import include_private_teams, load_private_teams
    private, urls, sources = load_private_teams(2026)
    northpoint = next(team for team in private if team.team_id == "northpoint-christian")
    assert (northpoint.classification, northpoint.association, northpoint.region) == ("Private", "TSSAA", "")
    assert "/ms/southaven/" in urls[northpoint.team_id]
    assert sum(team.association == "MAIS" for team in private) == 21
    assert sources["mais"]
    mhsaa = Team("tupelo-christian", "Tupelo Christian Prep", "1A", "3")
    combined = include_private_teams([mhsaa], private)
    assert combined[0] == mhsaa
    assert len({team.team_id for team in combined}) == len(combined)


def test_private_teams_rank_in_same_overall_calculation_and_unplayed_teams_wait():
    from mvpi.ranking import rank
    teams = [Team("public", "Public", "4A", "1"),
             Team("mais", "MAIS School", "Private", "", "MAIS"),
             Team("northpoint", "Northpoint Christian", "Private", "", "TSSAA"),
             Team("waiting", "Waiting", "Private", "", "MAIS")]
    matches = [Match("one", "mais", "public", 3, 0), Match("two", "northpoint", "mais", 3, 1)]
    rows = rank(teams, matches, {})
    assert {row.team_id for row in rows} == {"public", "mais", "northpoint"}
    assert [row.rank for row in rows] == [1, 2, 3]
    assert all(row.classification == "Private" for row in rows if row.association != "MHSAA")
    assert next(row for row in rows if row.team_id == "northpoint").to_dict()["association"] == "TSSAA"


def test_private_schedules_are_fetched_without_fabricating_media_rank(monkeypatch, tmp_path):
    from mvpi import maxpreps
    team = Team("waiting", "Waiting", "Private", "", "MAIS")
    url = "https://www.maxpreps.com/ms/example/waiting/volleyball/"
    requested = []
    monkeypatch.setattr(maxpreps, "_request", lambda address: requested.append(address) or "<html></html>")
    matches, failures = maxpreps.fetch_schedules([team], {}, tmp_path, team_urls={team.team_id: url})
    assert requested == [url + "schedule/"]
    assert matches == [] and failures == []


def test_private_membership_requires_season_review():
    import pytest
    from mvpi.private import load_private_teams
    with pytest.raises(ValueError, match="needs review"):
        load_private_teams(2027)


def test_schedule_season_filter_rejects_old_and_future_results():
    from datetime import date
    from calculate_volleyball import current_season_matches
    matches = [Match(str(year), "a", "b", 3, 0, played_at=datetime(year, 8, 1, tzinfo=timezone.utc))
               for year in (2025, 2026, 2027)]
    assert current_season_matches(matches, date(2026, 9, 5)) == [matches[1]]


def test_out_of_state_school_cannot_match_same_named_mississippi_school():
    from mvpi.maxpreps import _resolve_team
    ms = Team("oxford", "Oxford", "7A", "1")
    tn_url = "https://www.maxpreps.com/tn/example/oxford/volleyball/"
    assert _resolve_team("Oxford", tn_url, {"oxford": ms}, {}) == "external:/tn/example/oxford/volleyball"
    assert _resolve_team("Oxford", "", {"oxford": ms}, {}) == "oxford"


def test_external_parser_uses_exact_school_computer_rating_not_state_rank():
    import json
    from datetime import date
    from mvpi.external import parse_external_rating
    url = "https://www.maxpreps.com/tn/example/opponent/volleyball/"
    entry = {"teamCanonicalUrl": url, "year": "26-27", "rating": 12.8, "rank": 45,
             "schoolName": "Opponent", "schoolState": "TN"}
    def html(row):
        data = {"props": {"pageProps": {"rankingsData": {"notes": ["Last update: 9/3/2026"],
                "contexts": [{"entries": [row]}]}}}}
        return '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(data) + '</script>'
    result = parse_external_rating(html(entry), url, 2026, date(2026, 9, 5))
    assert result["rating"] == 12.8
    import pytest
    for change in [{"year": "25-26"}, {"teamCanonicalUrl": url.replace("opponent", "other")}, {"rating": None}]:
        with pytest.raises(ValueError):
            parse_external_rating(html({**entry, **change}), url, 2026, date(2026, 9, 5))
    with pytest.raises(ValueError, match="stale"):
        parse_external_rating(html(entry), url, 2026, date(2026, 10, 1))


def test_external_rating_calibration_matches_internal_scale_and_requires_evidence():
    from mvpi.ranking import calibrate_external_ratings
    media = {str(i): MediaRanking(100-i, str(i), "5-0", float(i), 0, "") for i in range(10)}
    baseline = {str(i): 0.2*i-1 for i in range(10)}
    contests = {str(i): [None]*5 for i in range(10)}
    anchors, audit = calibrate_external_ratings(media, baseline, contests, {"tn": 15})
    assert abs(anchors["tn"] - 2) < 1e-10
    assert audit["equivalent_matches"] == 8
    assert calibrate_external_ratings(media, baseline, {}, {"tn": 15})[0] == {}


def test_external_prior_influence_fades_as_imported_results_increase():
    from mvpi.ranking import _solve_ratings
    def difference(count):
        games = [Match(str(i), "ms", "tn", 3, 0) for i in range(count)]
        by_team = {"ms": games, "tn": games}
        high = _solve_ratings({"ms", "tn"}, {"ms"}, by_team, {"tn": 2}, {"tn"})
        low = _solve_ratings({"ms", "tn"}, {"ms"}, by_team, {"tn": -2}, {"tn"})
        return high["tn"] - low["tn"]
    assert difference(1) > difference(20) > 0


def test_embedded_schedule_imports_completed_tournament_not_future_or_duplicate():
    import json
    team = Team("northpoint", "Northpoint Christian", "Private", "", "TSSAA")
    source = "https://www.maxpreps.com/ms/southaven/northpoint/volleyball/"
    opponent = "https://www.maxpreps.com/tn/brighton/brighton/volleyball/"
    def side(url, name, score, result):
        data = [None]*17
        data[5], data[6], data[13], data[14] = result, score, url, name
        return data
    contest = [None]*30
    contest[0] = [side(source, team.name, 2, "W"), side(opponent, "Brighton", 0, "L")]
    contest[1], contest[11], contest[15], contest[29] = "tournament", "2026-08-21T17:30:00", 4, "neutral tournament"
    future = list(contest)
    future[1], future[15] = "future", 1
    data = {"props": {"pageProps": {"contests": [contest, contest, future]}}}
    html = '<script id="__NEXT_DATA__">' + json.dumps(data) + '</script>'
    matches = parse_schedule(html, source_team=team, source_url=source,
                             official_by_name={}, official_by_url={source.rstrip('/').replace('https://www.maxpreps.com',''): team})
    assert len(matches) == 1
    assert matches[0].perspective("northpoint")[1:3] == (2, 0)
    assert matches[0].away_team_url == opponent


def test_external_fetch_reports_missing_rating_and_reuses_only_recent_cache(monkeypatch, tmp_path):
    import json
    from datetime import date
    from mvpi import external
    url = "https://www.maxpreps.com/tn/example/opponent/volleyball/"
    match = Match("one", "ms", "external:tn", 3, 0, away_team_url=url)
    def fail(_):
        raise ValueError("not available")
    monkeypatch.setattr(external, "_request", fail)
    path = tmp_path / "ratings.json"
    result = external.fetch_external_ratings([match], {"ms"}, path, date(2026, 9, 5))
    assert result["external:tn"]["status"] == "unavailable"
    cached = {"external:tn": {"season": 2026, "rating": 10, "source_url": url+'rankings/', "source_updated_at": "2026-09-03"}}
    path.write_text(json.dumps(cached))
    assert external.fetch_external_ratings([match], {"ms"}, path, date(2026, 9, 5))["external:tn"]["status"] == "cached"
    assert external.fetch_external_ratings([match], {"ms"}, path, date(2026, 10, 1))["external:tn"]["status"] == "unavailable"


def test_full_ranking_credits_stronger_external_opponent_without_ranking_it():
    from mvpi.ranking import rank
    teams = [Team(f"ms{i}", f"School {i}", "4A", "1") for i in range(12)]
    matches = [Match(f"{i}-{j}", f"ms{i}", f"ms{j}", 3, 0)
               for i in range(12) for j in range(i)]
    matches.append(Match("cross-state", "ms8", "external:tn", 1, 3))
    media = {f"ms{i}": MediaRanking(12-i, f"School {i}", f"{i}-{11-i}", i*3.0-15, 0, "") for i in range(12)}
    audit = {}
    high = rank(teams, matches, {}, media, {"external:tn": 30}, audit)
    low = rank(teams, matches, {}, media, {"external:tn": -30})
    assert audit["status"] == "calibrated"
    assert next(row for row in high if row.team_id == "ms8").mvpi > next(row for row in low if row.team_id == "ms8").mvpi
    assert {row.team_id for row in high} == {team.team_id for team in teams}


# The public table is a regression fixture, not a fallback data source.
def _official_fixture():
    from pathlib import Path
    return (Path(__file__).parent / 'fixtures/mhsaa-volleyball-regions.html').read_text()


def test_official_classification_public_table_and_identity():
    from mvpi.live import _classification_rows, _validate_classifications
    teams, rows = _classification_rows(_official_fixture())
    _validate_classifications(teams)
    assert len(teams) == 226
    assert rows > len(teams)
    assert next(t for t in teams if t.team_id == 'lewisburg') == Team('lewisburg', 'Lewisburg High School', '7A', '1')


def _official_response(body, status=200, content_type='text/html; charset=UTF-8', url=None):
    from io import BytesIO
    from mvpi.live import CLASSIFICATIONS_URL
    response = BytesIO(body.encode())
    response.status = status
    response.headers = {'Content-Type': content_type}
    response.geturl = lambda: url or CLASSIFICATIONS_URL
    return response


def test_official_fetch_retries_empty_success_and_records_evidence(monkeypatch, tmp_path):
    import json
    from mvpi import live
    responses = iter([_official_response(''), _official_response(_official_fixture())])
    monkeypatch.setattr(live, 'urlopen', lambda *a, **k: next(responses))
    waits = []
    monkeypatch.setattr(live.time, 'sleep', waits.append)
    assert len(live.fetch_teams(tmp_path)) == 226
    audit = json.loads((tmp_path / 'response.json').read_text())['attempts']
    assert len(audit) == 2 and waits == [2]
    assert audit[0]['http_status'] == 200 and audit[0]['body_bytes'] == 0
    assert audit[0]['parsed_teams'] == 0 and audit[0]['failure_kind'] == 'incomplete_classifications'
    assert audit[1]['parsed_teams'] == 226 and 'failure_kind' not in audit[1]
    assert (tmp_path / 'attempt-1.html').read_bytes() == b''


def test_official_fetch_incomplete_exhaustion_keeps_snapshot(monkeypatch, tmp_path):
    import json
    import pytest
    import calculate_volleyball
    from mvpi import live
    monkeypatch.chdir(tmp_path)
    snapshot = tmp_path / 'data/volleyball/current.json'
    snapshot.parent.mkdir(parents=True)
    snapshot.write_text('previous valid snapshot')
    schedule = snapshot.with_name('matches.json')
    schedule.write_text('previous valid matches')
    requests = []
    def request(*args, **kwargs):
        requests.append(args)
        return _official_response('<title>Empty article</title><table></table>')
    monkeypatch.setattr(live, 'urlopen', request)
    monkeypatch.setattr(live.time, 'sleep', lambda _: None)
    with pytest.raises(ValueError, match='after 3 attempt'):
        calculate_volleyball.main()
    assert len(requests) == 3
    assert snapshot.read_text() == 'previous valid snapshot'
    assert schedule.read_text() == 'previous valid matches'
    audit = json.loads((tmp_path / 'work/classifications/response.json').read_text())
    assert audit['attempts'][-1]['title'] == 'Empty article'


def test_official_fetch_challenge_fails_without_bypass(monkeypatch, tmp_path):
    import pytest
    from mvpi import live
    requests = []
    def request(*args, **kwargs):
        requests.append(args)
        return _official_response('<title>Just a moment...</title><script src="/cf-chl-test"></script>')
    monkeypatch.setattr(live, 'urlopen', request)
    monkeypatch.setattr(live.time, 'sleep', lambda _: pytest.fail('Challenge must not be retried'))
    with pytest.raises(ValueError, match='challenge page'):
        live.fetch_teams(tmp_path)
    assert len(requests) == 1


def test_official_fetch_transient_http_and_transport_retry(monkeypatch, tmp_path):
    from urllib.error import HTTPError, URLError
    from io import BytesIO
    from mvpi import live
    outcomes = iter([URLError('temporary network failure'),
                     HTTPError(live.CLASSIFICATIONS_URL, 503, 'Unavailable',
                               {'Content-Type': 'text/html'}, BytesIO(b'<title>Unavailable</title>')),
                     _official_response(_official_fixture())])
    def request(*args, **kwargs):
        item = next(outcomes)
        if isinstance(item, Exception):
            raise item
        return item
    monkeypatch.setattr(live, 'urlopen', request)
    monkeypatch.setattr(live.time, 'sleep', lambda _: None)
    assert len(live.fetch_teams(tmp_path)) == 226
    assert 'http_error' in (tmp_path / 'response.json').read_text()


def test_official_fetch_rejects_wrong_content_or_location(monkeypatch, tmp_path):
    import pytest
    from mvpi import live
    monkeypatch.setattr(live.time, 'sleep', lambda _: pytest.fail('Permanent failure must not be retried'))
    for response in [_official_response(_official_fixture(), content_type='application/json'),
                     _official_response(_official_fixture(), url='https://www.misshsaa.com/login/'),
                     _official_response(_official_fixture(), status=403)]:
        monkeypatch.setattr(live, 'urlopen', lambda *a, **k: response)
        with pytest.raises(ValueError, match='after 1 attempt'):
            live.fetch_teams(tmp_path)


def test_official_validation_rejects_partial_duplicate_and_invalid_inventory():
    import pytest
    from mvpi.live import _classification_rows, _validate_classifications
    teams, _ = _classification_rows(_official_fixture())
    for invalid, message in [(teams[:119], 'only 119'),
                             ([t for t in teams if t.classification != '1A'], 'seven classes'),
                             (teams + [teams[0]], 'duplicate'),
                             (teams + [Team('invalid', 'Invalid', '1A', '9')], 'invalid school')]:
        with pytest.raises(ValueError, match=message):
            _validate_classifications(invalid)


def test_incomplete_refresh_cannot_replace_valid_snapshot(tmp_path):
    from datetime import date
    import json
    from types import SimpleNamespace
    import pytest
    from calculate_volleyball import _validate_refresh
    output = tmp_path / 'current.json'
    output.write_text(json.dumps({'metadata': {'generated_at': '2026-10-02',
                                              'ranked_teams': 247, 'completed_matches': 2907}}))
    fresh = SimpleNamespace(used_cache=False)
    cached = SimpleNamespace(used_cache=True)
    for media, classes, failures, ranks, matches in [
        (cached, fresh, [], 247, 2907), (fresh, cached, [], 247, 2907),
        (fresh, fresh, ['School'], 247, 2907), (fresh, fresh, [], 180, 2907),
        (fresh, fresh, [], 247, 2000), (fresh, fresh, [], 247, 0),
    ]:
        with pytest.raises(ValueError, match='Incomplete source refresh'):
            _validate_refresh(media, classes, failures, [None]*ranks, [None]*matches, output, date(2026, 10, 3))
    _validate_refresh(fresh, fresh, [], [None]*247, [None]*2907, output, date(2026, 10, 3))
    assert json.loads(output.read_text())['metadata']['generated_at'] == '2026-10-02'


def test_official_http_202_siteground_challenge_is_diagnosed(monkeypatch, tmp_path):
    import json
    from pathlib import Path
    import pytest
    from mvpi import live
    html = (Path(__file__).parent / 'fixtures/mhsaa-siteground-challenge.html').read_text()
    monkeypatch.setattr(live, 'urlopen', lambda *a, **k: _official_response(html, status=202))
    monkeypatch.setattr(live.time, 'sleep', lambda _: pytest.fail('Challenge must not be retried'))
    with pytest.raises(ValueError, match='challenge page'):
        live.fetch_teams(tmp_path)
    audit = json.loads((tmp_path / 'response.json').read_text())['attempts']
    assert len(audit) == 1
    assert audit[0]['http_status'] == 202
    assert audit[0]['failure_kind'] == 'upstream_challenge'
    assert audit[0]['parsed_teams'] == 0


def _captured_classifications(monkeypatch, tmp_path):
    from mvpi import live
    from mvpi import classifications
    from mvpi.classifications import fetch_classifications
    class CaptureClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(live, 'datetime', CaptureClock)
    monkeypatch.setattr(classifications, 'datetime', CaptureClock)
    cache = tmp_path / 'official.json'
    diagnostics = tmp_path / 'diagnostics'
    monkeypatch.setattr(live, 'urlopen', lambda *a, **k: _official_response(_official_fixture()))
    result = fetch_classifications(cache, diagnostics)
    assert not result.audit['used_cache']
    return cache, diagnostics, result


def test_classification_challenge_reuses_verified_capture_without_retry_or_redating(monkeypatch, tmp_path):
    import json
    from mvpi import live
    from mvpi.classifications import fetch_classifications
    cache, diagnostics, fresh = _captured_classifications(monkeypatch, tmp_path)
    original = cache.read_bytes()
    requests = []
    def challenge(*args, **kwargs):
        requests.append(args)
        return _official_response('<script>location="/.well-known/sgcaptcha/"</script>', status=202)
    monkeypatch.setattr(live, 'urlopen', challenge)
    monkeypatch.setattr(live.time, 'sleep', lambda _: __import__('pytest').fail('Do not retry challenges'))
    result = fetch_classifications(cache, diagnostics)
    assert result.teams == fresh.teams and len(result.teams) == 226
    assert result.audit['used_cache'] and result.audit['fallback_reason'] == 'upstream_challenge'
    assert result.audit['retrieved_at'] == fresh.audit['retrieved_at']
    assert result.audit['expires_at'] == fresh.audit['expires_at']
    assert cache.read_bytes() == original and len(requests) == 1
    assert json.loads((diagnostics / 'response.json').read_text())['classification_fetch'] == result.audit


def test_classification_cache_age_cycle_provenance_and_inventory_fail_closed(monkeypatch, tmp_path):
    import copy
    import json
    import pytest
    import hashlib
    from datetime import timedelta
    from mvpi.classifications import _validate_capture
    cache, _, _ = _captured_classifications(monkeypatch, tmp_path)
    original = json.loads(cache.read_text())
    captured = datetime.fromisoformat(original['response']['retrieved_at'])
    assert len(_validate_capture(original, captured + timedelta(days=7))[0]) == 226
    for now in (captured + timedelta(days=7, seconds=1), captured - timedelta(seconds=1),
                datetime(2027, 7, 1, tzinfo=timezone.utc)):
        with pytest.raises(ValueError):
            _validate_capture(original, now)
    changes = [({'cycle': '2027-29'}, {}), ({'schema_version': 2}, {}),
               ({'html': original['html'] + 'changed'}, {}),
               ({}, {'http_status': 202}), ({}, {'final_url': 'https://example.com/'}),
               ({}, {'requested_url': 'https://example.com/'}),
               ({}, {'content_type': 'application/json'}), ({}, {'body_sha256': 'invalid'}),
               ({}, {'retrieved_at': '2026-10-07'}), ({}, {'parsed_teams': 120}),
               ({}, {'failure_kind': 'upstream_challenge'})]
    for top, response in changes:
        payload = copy.deepcopy(original)
        payload.update(top)
        payload['response'].update(response)
        with pytest.raises(ValueError):
            _validate_capture(payload, captured)
    # A valid checksum cannot make an incomplete/duplicate/wrong-cycle table usable.
    for html in ('<table></table>', original['html'].replace('2025-27', '2027-29'),
                 original['html'] + '<table><tr><td>LEWISBURG HIGH SCHOOL</td><td>7</td><td>1</td></tr></table>'):
        payload = copy.deepcopy(original)
        payload['html'] = html
        payload['response'].update(body_bytes=len(html.encode()), body_sha256=hashlib.sha256(html.encode()).hexdigest())
        with pytest.raises(ValueError):
            _validate_capture(payload, captured)


def test_classification_cache_cannot_hide_changed_or_denied_source(monkeypatch, tmp_path):
    import pytest
    from mvpi import live
    from mvpi.classifications import fetch_classifications
    cache, diagnostics, _ = _captured_classifications(monkeypatch, tmp_path)
    original = cache.read_bytes()
    monkeypatch.setattr(live.time, 'sleep', lambda _: None)
    for html, options in [('<table></table>', {}),
                          (_official_fixture(), {'status': 403}),
                          (_official_fixture(), {'status': 503}),
                          (_official_fixture(), {'url': 'https://www.misshsaa.com/login/'}),
                          (_official_fixture(), {'content_type': 'application/json'})]:
        monkeypatch.setattr(live, 'urlopen', lambda *a, **k: _official_response(html, **options))
        with pytest.raises(ValueError, match='Official classification fetch failed'):
            fetch_classifications(cache, diagnostics)
        assert cache.read_bytes() == original


def test_classification_outage_requires_valid_cache_and_restored_source_updates_it(monkeypatch, tmp_path):
    import json
    import pytest
    from urllib.error import URLError
    from mvpi import live
    from mvpi.classifications import fetch_classifications
    cache, diagnostics, _ = _captured_classifications(monkeypatch, tmp_path)
    original = cache.read_bytes()
    def unavailable(*a, **k):
        raise URLError('temporary outage')
    monkeypatch.setattr(live, 'urlopen', unavailable)
    waits = []
    monkeypatch.setattr(live.time, 'sleep', waits.append)
    result = fetch_classifications(cache, diagnostics)
    assert result.audit['used_cache'] and waits == [2, 4]
    assert cache.read_bytes() == original
    payload = json.loads(original)
    payload['response']['retrieved_at'] = '2026-09-01T00:00:00+00:00'
    cache.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='cache rejected'):
        fetch_classifications(cache, diagnostics)
    cache.unlink()
    with pytest.raises(ValueError, match='cache rejected'):
        fetch_classifications(cache, diagnostics)
    monkeypatch.setattr(live, 'urlopen', lambda *a, **k: _official_response(_official_fixture()))
    restored = fetch_classifications(cache, diagnostics)
    assert not restored.audit['used_cache'] and len(restored.teams) == 226


def test_cached_classification_conflict_with_current_media_class_is_blocked():
    import pytest
    official = Team('lewisburg', 'Lewisburg High School', '7A', '1')
    row = ClassifiedMediaTeam('Lewisburg', 'https://www.maxpreps.com/ms/olive-branch/lewisburg/volleyball/', '6A')
    with pytest.raises(ValueError, match='conflicts with current class feed'):
        build_team_inventory([official], [row], require_class_agreement=True)
    assert build_team_inventory([official], [row])[0][0].classification == '7A'


def test_cached_classifications_keep_refresh_gates_and_publish_honest_audit(monkeypatch, tmp_path):
    import json
    import pytest
    from types import SimpleNamespace
    from datetime import date
    import calculate_volleyball as calculate
    from mvpi import live
    from mvpi.classifications import CACHE_PATH
    class CalculationDate(date):
        @classmethod
        def today(cls):
            return date(2026, 10, 7)
    monkeypatch.setattr(calculate, 'date', CalculationDate)
    cache, _, captured = _captured_classifications(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    CACHE_PATH.parent.mkdir(parents=True)
    CACHE_PATH.write_bytes(cache.read_bytes())
    monkeypatch.setattr(live, 'urlopen', lambda *a, **k: _official_response('sgcaptcha', status=202))
    signals = {team.team_id: MediaRanking(i, team.name, '3-0', 1, 1, '')
               for i, team in enumerate(captured.teams, 1)}
    media = SimpleNamespace(used_cache=False, source_updated_at=None, rankings=[])
    classes = SimpleNamespace(used_cache=False, teams=[])
    monkeypatch.setattr(calculate, 'fetch_rankings', lambda _: media)
    monkeypatch.setattr(calculate, 'fetch_classified_teams', lambda _: classes)
    monkeypatch.setattr(calculate, 'load_private_teams', lambda _: ([], {}, {}))
    monkeypatch.setattr(calculate, 'reconcile_rankings', lambda *a: (signals, []))
    played = datetime(2026, 8, 1, tzinfo=timezone.utc)
    match = Match('verified', captured.teams[0].team_id, captured.teams[1].team_id, 3, 1, played_at=played)
    monkeypatch.setattr(calculate, 'fetch_schedules', lambda *a, **k: ([match], []))
    monkeypatch.setattr(calculate, 'fetch_matches', lambda *a: ([], {}))
    monkeypatch.setattr(calculate, 'fetch_external_ratings', lambda *a: {})
    rows = [SimpleNamespace(team_id=team.team_id, team=team.name, classification=team.classification,
                            to_dict=lambda team=team: {'team': team.name, 'team_id': team.team_id})
            for team in captured.teams]
    monkeypatch.setattr(calculate, 'rank', lambda *a: rows)
    output = CACHE_PATH.with_name('current.json')
    schedule = CACHE_PATH.with_name('matches.json')
    output.write_text(json.dumps({'metadata': {'generated_at': '2026-10-07',
                                              'ranked_teams': 226, 'completed_matches': 1}}))
    schedule.write_text('previous valid schedule')
    original = output.read_bytes()
    for feed in (media, classes):
        feed.used_cache = True
        with pytest.raises(ValueError, match='Incomplete source refresh'):
            calculate.main()
        assert output.read_bytes() == original and schedule.read_text() == 'previous valid schedule'
        feed.used_cache = False
    calculate.main()
    audit = json.loads(output.read_text())['metadata']['classification_fetch']
    assert audit['used_cache'] and audit['retrieved_at'] == captured.audit['retrieved_at']
    assert audit['live_attempts'][0]['http_status'] == 202
    assert json.loads(schedule.read_text())['metadata']['matches'] == 1
    # Expiry fails before any ranking snapshot or schedule replacement.
    published, published_schedule = output.read_bytes(), schedule.read_bytes()
    payload = json.loads(CACHE_PATH.read_text())
    payload['response']['retrieved_at'] = '2026-09-01T00:00:00+00:00'
    CACHE_PATH.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='cache rejected'):
        calculate.main()
    assert output.read_bytes() == published and schedule.read_bytes() == published_schedule
