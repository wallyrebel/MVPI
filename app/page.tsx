'use client';

import { useState } from 'react';
import snapshot from '../data/volleyball/current.json';
import { siteUrl } from './site';

type Row = typeof snapshot.rankings[number];
const classes = ['7A', '6A', '5A', '4A', '3A', '2A', '1A', 'Private'] as const;
function teamLabel(row: Row) {
  return row.classification === 'Private'
    ? `Private · ${row.association}${row.association === 'TSSAA' ? ' · Southaven' : ''}`
    : `${row.classification} · Region ${row.region}`;
}

type Scope = typeof classes[number] | 'Overall';

function RankingRow({ row, displayRank = row.rank, classView = false }: { row: Row; displayRank?: number; classView?: boolean }) {
  return (
    <div className="vb-row">
      <strong className="vb-rank">{displayRank}</strong>
      <div className="vb-team"><strong>{row.team}</strong><small>{classView ? `State #${row.rank} · ${teamLabel(row)}` : teamLabel(row)}</small></div>
      <span>{row.record}</span>
      <strong className="vb-score">{row.mvpi.toFixed(1)}</strong>
      <span>{row.media_rank ? `#${row.media_rank}` : '—'}</span>
      <span>{row.sos.toFixed(1)}</span>
      <span>{row.sets_for}–{row.sets_against}</span>
      <span className="vb-coverage">{row.set_matches}/{row.matches}</span>
    </div>
  );
}

export default function Home() {
  const [scope, setScope] = useState<Scope>('7A');
  const [query, setQuery] = useState('');
  const rankedWithMatches = snapshot.rankings;
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const searching = normalizedQuery.length > 0;
  const displayed = searching
    ? rankedWithMatches.filter((row) => {
        const words = row.team.toLocaleLowerCase().match(/[a-z0-9]+/g) ?? [];
        const initials = words.map((word) => word[0]).join('');
        const searchText = `${row.team} ${row.team_id} ${row.classification} ${initials} ${initials}s`.toLocaleLowerCase();
        return searchText.includes(normalizedQuery);
      })
    : scope === 'Overall'
      ? rankedWithMatches
      : rankedWithMatches.filter((row) => row.classification === scope);
  const strongestSchedule = [...rankedWithMatches]
    .filter((row) => row.media_rank !== null)
    .sort((a, b) => b.sos - a.sos)[0];
  const publishedMatches = rankedWithMatches.reduce((sum, row) => sum + row.matches, 0);
  const setMatches = rankedWithMatches.reduce((sum, row) => sum + row.set_matches, 0);
  const generatedDate = new Date(`${snapshot.metadata.generated_at}T12:00:00`).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  const structuredData = [
    {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: 'Mississippi Volleyball Power Index',
      alternateName: ['MVPI', 'Mississippi Volleyball Rankings'],
      url: siteUrl,
    },
    {
      '@context': 'https://schema.org',
      '@type': 'Dataset',
      name: '2026 Mississippi Volleyball Rankings',
      alternateName: 'Mississippi Volleyball Power Index',
      description: 'Statewide, MHSAA 1A–7A and Private Mississippi high school volleyball rankings calculated from records, set scores, strength of schedule, opponent quality and recent results.',
      url: siteUrl,
      dateModified: snapshot.metadata.generated_at,
      temporalCoverage: '2026',
      spatialCoverage: { '@type': 'State', name: 'Mississippi' },
      creator: { '@type': 'Organization', name: 'Mississippi Volleyball Power Index', url: siteUrl },
      isAccessibleForFree: true,
      keywords: ['Mississippi volleyball rankings', 'Mississippi Volleyball Power Index', 'MHSAA volleyball rankings'],
      variableMeasured: ['Team record', 'Set scores', 'Strength of schedule', 'Opponent quality', 'Recent form'],
    },
    {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: 'Mississippi Volleyball Rankings',
      numberOfItems: rankedWithMatches.length,
      itemListOrder: 'https://schema.org/ItemListOrderAscending',
      itemListElement: rankedWithMatches.map((row) => ({
        '@type': 'ListItem',
        position: row.rank,
        item: {
          '@type': 'SportsTeam',
          name: row.team,
          sport: 'Volleyball',
          description: `${row.team} is ranked No. ${row.rank} in the Mississippi Volleyball Power Index with a ${row.record} record.`,
        },
      })),
    },
  ];
  return (
    <main className="vb-main">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData).replace(/</g, '\\u003c') }} />
      <header className="vb-header"><div className="vb-brand"><span>V</span><div><strong>Mississippi Volleyball</strong><small>POWER INDEX</small></div></div><div className="vb-live"><i />LIVE MEDIA DATA</div></header>
      <section className="vb-hero">
        <div><p className="vb-eyebrow">2026 · Updated <time dateTime={snapshot.metadata.generated_at}>{generatedDate}</time></p><h1>Mississippi Volleyball<br />Rankings</h1><p>The Mississippi Volleyball Power Index rates MHSAA 1A–7A teams, Mississippi MAIS programs and Northpoint Christian in Southaven from media records, match and set scores, media rank, strength of schedule, opponent quality, and recent form.</p></div>
        <aside><small>Current data pull</small><strong>{snapshot.metadata.media_schedule_matches.toLocaleString()} published match scores</strong><dl><div><dt>Eligible teams</dt><dd>{snapshot.metadata.teams}</dd></div><div><dt>Ranked now</dt><dd>{rankedWithMatches.length}</dd></div><div><dt>Updates</dt><dd>Tue · Fri · Sun</dd></div></dl></aside>
      </section>
      <section className="vb-callouts">
        <article><span>No. 1</span><strong>{snapshot.rankings[0].team}</strong><small>{snapshot.rankings[0].record} · MVPI {snapshot.rankings[0].mvpi.toFixed(1)}</small></article>
        <article><span>Strongest published schedule</span><strong>{strongestSchedule?.team}</strong><small>Media strength of schedule: {strongestSchedule?.sos.toFixed(1)}</small></article>
        <article><span>Set-score coverage</span><strong>{setMatches.toLocaleString()} of {publishedMatches.toLocaleString()} team-results</strong><small>Records stay authoritative even when a tournament has no public match-level set score</small></article>
      </section>
      <section className="vb-panel">
        <div className="vb-panel-title"><div><p className="vb-eyebrow">Live computer rankings</p><h2>{searching ? 'Team search' : scope === 'Overall' ? 'Statewide' : scope === 'Private' ? 'Private' : `Class ${scope}`}</h2></div><span>{searching ? `${displayed.length} matching team${displayed.length === 1 ? '' : 's'}` : 'Formula MVPI 0.3 · Media data authoritative'}</span></div>
        <div className="vb-team-search">
          <label htmlFor="team-search">Search teams</label>
          <div>
            <input id="team-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Team name or abbreviation (for example, TCPS)" autoComplete="off" />
            {searching && <button type="button" onClick={() => setQuery('')} aria-label="Clear team search">Clear</button>}
          </div>
        </div>
        <nav className="vb-class-tabs" aria-label="Classification rankings">
          {[...classes, 'Overall' as const].map((label) => (
            <button key={label} className={!searching && scope === label ? 'active' : ''} type="button" onClick={() => { setScope(label); setQuery(''); }}>{label}</button>
          ))}
        </nav>
        <div className="vb-table-wrap">
          <div className="vb-head vb-row"><span>{searching || scope === 'Overall' ? 'Rank' : 'Group rank'}</span><span>Team</span><span>Record</span><span>MVPI</span><span>Media rank</span><span>SOS</span><span>Sets</span><span>Set data</span></div>
          {displayed.map((row, index) => <RankingRow key={row.team_id} row={row} displayRank={searching || scope === 'Overall' ? row.rank : index + 1} classView={!searching && scope !== 'Overall'} />)}
          {displayed.length === 0 && <p className="vb-empty" role="status">No ranked teams match “{query.trim()}”.</p>}
        </div>
        <p className="vb-source-note">Private includes MAIS teams and Northpoint Christian (TSSAA). Schools without current-season results or a published ranking remain unranked. Record is the statewide media record. “Sets” totals publicly listed match scores; “Set data” shows how many published matches have usable set scores. Official association results only fill missing data and never override the media record.</p>
        <p className="vb-source-note">Out-of-state opponent ratings: {snapshot.metadata.external_opponents_rated} of {snapshot.metadata.external_opponents} available from MaxPreps. {snapshot.metadata.external_rating_calibration.status === 'calibrated' ? 'Ratings are blended with match results when calculating opponent strength.' : 'There is not enough reliable calibration data to apply external ratings yet; opponent strength uses imported results.'}
          {Object.values(snapshot.external_opponents).filter((opponent) => opponent.rating === null).map((opponent) => (
            <span key={opponent.source_url}> Rating unavailable for <a href={opponent.source_url} target="_blank" rel="noreferrer">{opponent.team.replaceAll('-', ' ')} ({opponent.state})</a>; its strength uses available results and a neutral starting estimate.</span>
          ))}
        </p>
      </section>
      <section className="vb-method"><div><p className="vb-eyebrow">How MVPI thinks</p><h2>Who you played matters.<br />How competitive you were matters too.</h2></div><p>Opponent-adjusted set performance contributes 35%, MVPI opponent strength 15%, record 10%, set percentage 10%, recent form 5%, media statewide rank 15%, and media schedule strength 10%. MHSAA enrollment class is only a fading early-season prior; Private teams start with a neutral prior. Out-of-state opponent strength uses MaxPreps computer ratings converted to the MVPI scale, blended with imported match results.</p></section>
      <section className="vb-seo" aria-labelledby="about-mvpi">
        <div><p className="vb-eyebrow">About the rankings</p><h2 id="about-mvpi">Mississippi Volleyball Power Index</h2><p>MVPI is an independent computer rating of Mississippi high school volleyball teams. It combines results and opponent quality so the statewide order reflects more than win-loss record alone.</p></div>
        <div><h3>MHSAA classes and Private rankings</h3><p>The page includes Mississippi volleyball rankings for 1A, 2A, 3A, 4A, 5A, 6A and 7A, plus a separate Private group for Mississippi MAIS schools and Northpoint Christian (TSSAA). All groups share the same overall statewide calculation. Private is a display group, not an official association class.</p><h3>Updated three times each week</h3><p>Published records, scores and set results are refreshed Tuesday, Friday and Sunday during the season. The visible update date and sitemap change with every completed data run.</p></div>
      </section>
      <footer><span>MVPI · Mississippi Volleyball Power Index</span><span>Media records and results · MHSAA 1A–7A · MAIS · Northpoint Christian</span></footer>
    </main>
  );
}
