# Mississippi Volleyball Power Index (MVPI)

MVPI is an explainable ranking of Mississippi MHSAA volleyball teams in Classes 1A–7A. It uses authoritative media records, match and set scores, media rank, strength of schedule, opponent-adjusted performance, set percentage, and recent form.

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
