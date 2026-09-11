import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { SiteFooter, SiteHeader } from '../../site-nav';
import { siteUrl } from '../../site';
import {
  classPeers,
  classRank,
  formatDate,
  generatedAt,
  getTeam,
  longDate,
  rankings,
  teamSchedule,
  type Ranking,
  type TeamMatch,
} from '../../team-data';

type Params = { params: Promise<{ teamId: string }> };

export function generateStaticParams() {
  return rankings.map((row) => ({ teamId: row.team_id }));
}

function groupLabel(row: Ranking) {
  return row.classification === 'Private'
    ? `Private (${row.association})`
    : `Class ${row.classification}${row.region ? `, Region ${row.region}` : ''}`;
}

function summarize(row: Ranking, games: TeamMatch[]) {
  const wins = games.filter((game) => game.won);
  const losses = games.filter((game) => !game.won);
  const ranked = (game: TeamMatch) => game.opponentRank !== null;
  const bestWin = wins.filter(ranked).sort((a, b) => a.opponentRank! - b.opponentRank!)[0];
  const worstLoss = losses.filter(ranked).sort((a, b) => b.opponentRank! - a.opponentRank!)[0];
  const last5 = games.slice(-5);
  const last5Wins = last5.filter((game) => game.won).length;
  return { wins, losses, bestWin, worstLoss, last5, last5Wins };
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { teamId } = await params;
  const row = getTeam(teamId);
  if (!row) return {};
  const title = `${row.team} Volleyball — Rankings, Record & Schedule`;
  const description = `${row.team} is No. ${row.rank} in the 2026 Mississippi Volleyball Power Index at ${row.record} (${groupLabel(row)}). Full schedule, set scores, strength of schedule and rating breakdown.`;
  return {
    title,
    description,
    alternates: { canonical: `/team/${row.team_id}` },
    openGraph: {
      type: 'article',
      url: `${siteUrl}/team/${row.team_id}`,
      title,
      description,
    },
    twitter: { card: 'summary_large_image', title, description },
  };
}

export default async function TeamPage({ params }: Params) {
  const { teamId } = await params;
  const row = getTeam(teamId);
  if (!row) notFound();

  const games = teamSchedule(teamId);
  const { wins, losses, bestWin, worstLoss, last5, last5Wins } = summarize(row, games);
  const peers = classPeers(row.classification);
  const withinClass = classRank(row);
  const overall = rankings.findIndex((peer) => peer.team_id === row.team_id);
  const ahead = rankings[overall - 1];
  const behind = rankings[overall + 1];
  const setDiff = row.sets_for - row.sets_against;

  const components: Array<[string, number, string]> = [
    ['Opponent-adjusted set performance', 35, 'How well the team performed per set, adjusted for opponent quality.'],
    ['MVPI opponent strength', 15, 'Average MVPI rating of every opponent played.'],
    ['Media statewide rank', 15, 'Published statewide ordinal rank, as a percentile.'],
    ['Record', 10, 'Win percentage from the authoritative media record.'],
    ['Set percentage', 10, 'Share of all sets won across published match scores.'],
    ['Media schedule strength', 10, 'Published strength-of-schedule field.'],
    ['Recent form', 5, 'Opponent-adjusted performance across the last five matches.'],
  ];

  const structuredData = {
    '@context': 'https://schema.org',
    '@type': 'SportsTeam',
    name: row.team,
    sport: 'Volleyball',
    url: `${siteUrl}/team/${row.team_id}`,
    memberOf: { '@type': 'SportsOrganization', name: row.association },
    description: `${row.team} is ranked No. ${row.rank} of ${rankings.length} in the Mississippi Volleyball Power Index with a ${row.record} record.`,
  };

  return (
    <main className="vb-main">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData).replace(/</g, '\\u003c') }} />
      <SiteHeader />

      <nav className="vb-crumbs" aria-label="Breadcrumb">
        <Link href="/">Rankings</Link> <span>/</span> <span>{row.team}</span>
      </nav>

      <section className="vb-team-hero">
        <div>
          <p className="vb-eyebrow">{groupLabel(row)} · Updated <time dateTime={generatedAt}>{longDate(generatedAt)}</time></p>
          <h1>{row.team}</h1>
          <p className="vb-team-lede">
            {row.team} is <strong>No. {row.rank}</strong> of {rankings.length} ranked teams in the 2026 Mississippi
            Volleyball Power Index, and <strong>No. {withinClass}</strong> of {peers.length} in {row.classification === 'Private' ? 'the Private group' : `Class ${row.classification}`}.
            The team is {row.record} across {row.matches} published matches with a {row.sets_for}–{row.sets_against} set
            record ({setDiff >= 0 ? '+' : ''}{setDiff}).
          </p>
          <p className="vb-team-lede">
            {bestWin
              ? <>Its best result is a {bestWin.setsFor}–{bestWin.setsAgainst} win over <Link href={`/team/${bestWin.opponentId}`}>{bestWin.opponent}</Link> (No. {bestWin.opponentRank}) on {formatDate(bestWin.date)}. </>
              : <>It has not yet beaten a ranked Mississippi opponent. </>}
            {worstLoss
              ? <>Its toughest setback was {worstLoss.setsFor}–{worstLoss.setsAgainst} against <Link href={`/team/${worstLoss.opponentId}`}>{worstLoss.opponent}</Link> (No. {worstLoss.opponentRank}). </>
              : null}
            {last5.length > 0 && <>Over the last {last5.length} matches it is {last5Wins}–{last5.length - last5Wins}.</>}
          </p>
        </div>
        <aside className="vb-team-card">
          <small>MVPI rating</small>
          <strong>{row.mvpi.toFixed(1)}</strong>
          <dl>
            <div><dt>Statewide</dt><dd>No. {row.rank}</dd></div>
            <div><dt>{row.classification === 'Private' ? 'Private' : row.classification}</dt><dd>No. {withinClass}</dd></div>
            <div><dt>Record</dt><dd>{row.record}</dd></div>
            <div><dt>Sets</dt><dd>{row.sets_for}–{row.sets_against}</dd></div>
            <div><dt>Strength of schedule</dt><dd>{row.sos.toFixed(1)}</dd></div>
            <div><dt>Opponent MVPI</dt><dd>{row.opponent_sos.toFixed(1)}</dd></div>
            <div><dt>Media rank</dt><dd>{row.media_rank ? `No. ${row.media_rank}` : '—'}</dd></div>
            <div><dt>Set data</dt><dd>{row.set_matches}/{row.matches}</dd></div>
          </dl>
        </aside>
      </section>

      <section className="vb-panel">
        <div className="vb-panel-title">
          <div><p className="vb-eyebrow">2026 season</p><h2>Schedule &amp; results</h2></div>
          <span>{wins.length}–{losses.length} · {games.length} matches with published scores</span>
        </div>
        <div className="vb-table-wrap vb-sched-wrap">
          <div className="vb-head vb-sched-row"><span>Date</span><span>Opponent</span><span>Site</span><span>Result</span><span>Sets</span><span>Opp. MVPI</span></div>
          {games.map((game, index) => (
            <div className="vb-sched-row" key={`${game.date}-${game.opponentId}-${index}`}>
              <span className="tabular">{formatDate(game.date)}</span>
              <span className="vb-sched-opp">
                {game.opponentRank !== null
                  ? <Link href={`/team/${game.opponentId}`}>{game.opponent}</Link>
                  : <span>{game.opponent}</span>}
                {game.opponentRank !== null && <small>No. {game.opponentRank}</small>}
                {game.tournament && <small>Tournament</small>}
              </span>
              <span className="vb-sched-site">{game.site}</span>
              <span className={game.won ? 'vb-win' : 'vb-loss'}>{game.won ? 'W' : 'L'}</span>
              <span className="tabular">{game.setsFor}–{game.setsAgainst}</span>
              <span className="tabular">{game.opponentMvpi !== null ? game.opponentMvpi.toFixed(1) : '—'}</span>
            </div>
          ))}
          {games.length === 0 && <p className="vb-empty">No published match scores for {row.team} this season yet.</p>}
        </div>
        <p className="vb-source-note">
          Results come from published media schedules, with official association results used only to fill matches the
          media feed does not list. Matches without a public set score still count toward the record.
        </p>
      </section>

      <section className="vb-breakdown">
        <div>
          <p className="vb-eyebrow">Why {row.team} rates {row.mvpi.toFixed(1)}</p>
          <h2>Rating breakdown</h2>
          <p>
            Every component below is converted to a statewide percentile among ranked teams, then weighted. That is why a
            team can hold a strong record and still rate behind a team with more losses against a harder schedule.
          </p>
        </div>
        <ul className="vb-weights">
          {components.map(([label, weight, note]) => (
            <li key={label}><strong>{weight}%</strong><span>{label}</span><small>{note}</small></li>
          ))}
        </ul>
      </section>

      <section className="vb-neighbors">
        <h2>Nearby in the statewide rankings</h2>
        <div>
          {ahead && <Link href={`/team/${ahead.team_id}`}><small>No. {ahead.rank} · ahead</small><strong>{ahead.team}</strong><span>{ahead.record} · MVPI {ahead.mvpi.toFixed(1)}</span></Link>}
          {behind && <Link href={`/team/${behind.team_id}`}><small>No. {behind.rank} · behind</small><strong>{behind.team}</strong><span>{behind.record} · MVPI {behind.mvpi.toFixed(1)}</span></Link>}
        </div>
        <h2>Others in {row.classification === 'Private' ? 'the Private group' : `Class ${row.classification}`}</h2>
        <div className="vb-peer-list">
          {peers.filter((peer) => peer.team_id !== row.team_id).slice(0, 12).map((peer) => (
            <Link key={peer.team_id} href={`/team/${peer.team_id}`}>{peer.team}</Link>
          ))}
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}
