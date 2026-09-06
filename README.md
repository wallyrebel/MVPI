# Mississippi Volleyball Power Index (MVPI)

MVPI is an explainable ranking of Mississippi MHSAA volleyball teams in Classes 1A–7A, plus a separate **Private** group for Mississippi MAIS schools and Northpoint Christian in Southaven (TSSAA). All teams participate in the same Overall rankings. It uses authoritative media records, match and set scores, media rank, strength of schedule, opponent-adjusted performance, set percentage, and recent form.

## Ranking model

- 35% opponent-adjusted set performance
- 15% MVPI opponent strength
- 15% media statewide rank
- 10% media strength of schedule
- 10% record
- 10% set percentage
- 5% recent form

Enrollment class is only a fading early-season prior. A competitive five-set loss to an elite opponent can therefore rate more favorably than an easy sweep of a weak opponent.

## Local setup

Requirements: Python 3.12+, Node.js 22+, and npm.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm install
python calculate_volleyball.py
python -m pytest -q
npm run dev -- --port 4322
```

## Automated updates

`.github/workflows/update-rankings.yml` refreshes results every Tuesday, Friday, and Sunday afternoon, validates the ranking engine, verifies the production build, and commits an updated `data/volleyball/current.json` when the rankings change.

## Cloudflare Workers

The application builds to a Cloudflare Worker with static assets.

- Build command: `npm run build`
- Deploy command: `npx wrangler deploy --config dist/server/wrangler.json`
- Production branch: `main`

## Repository map

```text
app/                         local ranking dashboard
mfpi/                        providers, matching, validation, SRS, formula, storage
tests/                       unit, integration, and ranking-scenario tests
scripts/run_weekly.ps1       one-command local weekly workflow
data/current/                viewer's latest live or validated rankings
data/2026/week-XX/           immutable official snapshots
calculate_rankings.py        CLI entry point
METHODOLOGY.md               formula in plain language and exact weights
DATA_SOURCES.md              source contracts, permissions, and limitations
ADMIN_GUIDE.md               validation, corrections, and weekly operation
```

## Formula and auditability

Every component stores its raw value, normalized score, effective weight, and contribution. The unrounded contributions sum to MFPI; display values are rounded only at the edge. Formula version `MFPI-3.1` is stored in every snapshot and database run. Media Rank and Strength of Schedule contribute 10% each; MFPI's score-based model contributes the remaining 80%. Out-of-state opponents receive a published-rating SRS prior when available. See [METHODOLOGY.md](METHODOLOGY.md) for the full calculation.

## Tests

```powershell
python -m pytest -q
```

The suite covers margin diminishing returns, home field, SRS convergence, robust normalization, SOS, quality wins, weak schedules, close elite losses, recent form, dynamic/stale weights, aliases, ties, forfeits, zero-game teams, missing data, tie breakers, movement, class filtering, provider parsing, validation, and the 70-point-win scenario.

## Provisional rankings

The official MHSAA score center sometimes leaves completed-looking scheduled games without a verified final. MFPI checks a secondary public source only for those gaps, records every secondary result in the validation audit, and continues to prefer an official MHSAA final whenever one exists. MFPI still ranks every 1A–7A team from the verified results available and clearly marks the run provisional until at least 95% of expected games have verified scores. Impossible scores, conflicting secondary reports, ambiguous teams, duplicates, future results, and failed SRS convergence remain hard blockers.

## Private school coverage

`data/volleyball/private-schools.json` retains the verified 2026 MAIS volleyball school list, MaxPreps team URLs and association sources, plus Northpoint Christian. Out-of-state MAIS members remain opponents only. Existing MHSAA members keep their official classes. Private is a display group; its teams receive a neutral starting prior, not an invented MHSAA enrollment class.

The updater fetches every registered private school schedule even before it appears in the statewide MaxPreps rankings. Only current-season results count. Schools without results or a media ranking remain in the inventory and are listed in snapshot metadata as unranked. Membership must be reviewed when the season changes.

Sources: [MAIS 2026–27 volleyball alignment, pages 47–48](https://home.msais.org/postoffice/mailouts/aacminutes_102825_1761753701.pdf), [MAIS school list](https://home.msais.org/test2/index.php), [Northpoint TSSAA directory](https://portal.tssaa.org/common/directory/?id=472), and [MaxPreps Mississippi rankings](https://www.maxpreps.com/ms/volleyball/rankings/1/).

## Out-of-state opponent strength (MVPI 0.3)

Every completed imported schedule result preserves each school's MaxPreps URL. Out-of-state opponents use URL-based identities so a same-named Mississippi school cannot absorb their results. The importer also reads completed tournament results in MaxPreps' embedded schedule data when JSON-LD omits them.

For every out-of-state opponent with a known MaxPreps URL, the updater fetches its team rankings page and selects the exact school's current-season **computer rating**, never its state rank. Ratings must be dated within 14 days of the calculation date. A recent cached rating can be used after a fetch failure; unavailable and stale ratings are reported explicitly in the snapshot's `external_opponents` audit. Missing ratings keep the existing neutral prior. Opponents with no known source URL cannot receive a MaxPreps rating.

First, MVPI solves its existing set-based model. It then fits a linear conversion from MaxPreps computer ratings to that internal strength scale, using Mississippi teams with at least five imported results (at least ten calibration teams and a positive slope required). The conversion is fitted afresh for each update; it does not compare numerical state ranks. Calibration coefficients and each opponent's converted prior are saved in snapshot metadata.

A second solve uses each converted external rating as an eight-match prior: `(8 × converted rating + sum of opponent-adjusted imported performances) / (8 + imported match count)`, followed by the usual statewide centering. Thus one imported result gives the external rating 8/9 of the pre-centering estimate; eight give it half; more results gradually take precedence. Eight matches is a modeling choice, not a MaxPreps rule. Without sufficient calibration, external priors are not applied and the audit states why. The seven final component weights are unchanged. The existing Media SOS column remains MaxPreps' published schedule-strength value, not the internal opponent-strength percentile.

This applies to all ranked schools and affects opponent strength, adjusted performance and recent form. External schools remain opponents only; they do not enter Mississippi's Overall or Private tables. Source URLs, source dates, retrieval times and cache/unavailable flags are retained with the published snapshot.
