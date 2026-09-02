'use client';

import { useState } from 'react';
import snapshot from '../data/volleyball/current.json';

type Row = typeof snapshot.rankings[number];
const classes = ['7A', '6A', '5A', '4A', '3A', '2A', '1A'] as const;
type Scope = typeof classes[number] | 'Overall';

function RankingRow({ row, displayRank = row.rank, classView = false }: { row: Row; displayRank?: number; classView?: boolean }) {
  return (
    <div className="vb-row">
      <strong className="vb-rank">{displayRank}</strong>
      <div className="vb-team"><strong>{row.team}</strong><small>{classView ? `State #${row.rank} · Region ${row.region}` : `${row.classification} · Region ${row.region}`}</small></div>
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
  const rankedWithMatches = snapshot.rankings;
  const displayed = scope === 'Overall' ? rankedWithMatches : rankedWithMatches.filter((row) => row.classification === scope);
  const strongestSchedule = [...rankedWithMatches]
    .filter((row) => row.media_rank !== null)
    .sort((a, b) => b.sos - a.sos)[0];
  const publishedMatches = rankedWithMatches.reduce((sum, row) => sum + row.matches, 0);
  const setMatches = rankedWithMatches.reduce((sum, row) => sum + row.set_matches, 0);
  const generatedDate = new Date(`${snapshot.metadata.generated_at}T12:00:00`).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  return (
    <main className="vb-main">
      <header className="vb-header"><div className="vb-brand"><span>V</span><div><strong>Mississippi Volleyball</strong><small>POWER INDEX</small></div></div><div className="vb-live"><i />LIVE MEDIA DATA</div></header>
      <section className="vb-hero">
        <div><p className="vb-eyebrow">2026 · Updated {generatedDate}</p><h1>Mississippi Volleyball<br />Rankings</h1><p>All MHSAA 1A–7A programs with enough published data, rated from media records, match and set scores, media rank, strength of schedule, opponent quality, and recent form.</p></div>
        <aside><small>Current data pull</small><strong>{snapshot.metadata.media_schedule_matches.toLocaleString()} published match scores</strong><dl><div><dt>MHSAA teams</dt><dd>{snapshot.metadata.teams}</dd></div><div><dt>Ranked now</dt><dd>{rankedWithMatches.length}</dd></div><div><dt>Updates</dt><dd>Tue · Fri · Sun</dd></div></dl></aside>
      </section>
      <section className="vb-callouts">
        <article><span>No. 1</span><strong>{snapshot.rankings[0].team}</strong><small>{snapshot.rankings[0].record} · MVPI {snapshot.rankings[0].mvpi.toFixed(1)}</small></article>
        <article><span>Strongest published schedule</span><strong>{strongestSchedule?.team}</strong><small>Media strength of schedule: {strongestSchedule?.sos.toFixed(1)}</small></article>
        <article><span>Set-score coverage</span><strong>{setMatches.toLocaleString()} of {publishedMatches.toLocaleString()} team-results</strong><small>Records stay authoritative even when a tournament has no public match-level set score</small></article>
      </section>
      <section className="vb-panel">
        <div className="vb-panel-title"><div><p className="vb-eyebrow">Live computer rankings</p><h2>{scope === 'Overall' ? 'Statewide' : `Class ${scope}`}</h2></div><span>Formula MVPI 0.2 · Media data authoritative</span></div>
        <nav className="vb-class-tabs" aria-label="Classification rankings">
          {[...classes, 'Overall' as const].map((label) => (
            <button key={label} className={scope === label ? 'active' : ''} type="button" onClick={() => setScope(label)}>{label}</button>
          ))}
        </nav>
        <div className="vb-table-wrap">
          <div className="vb-head vb-row"><span>{scope === 'Overall' ? 'Rank' : 'Class rank'}</span><span>Team</span><span>Record</span><span>MVPI</span><span>Media rank</span><span>SOS</span><span>Sets</span><span>Set data</span></div>
          {displayed.map((row, index) => <RankingRow key={row.team_id} row={row} displayRank={scope === 'Overall' ? row.rank : index + 1} classView={scope !== 'Overall'} />)}
        </div>
        <p className="vb-source-note">Record is the statewide media record. “Sets” totals publicly listed match scores; “Set data” shows how many published matches have usable set scores. Official association results only fill missing data and never override the media record.</p>
      </section>
      <section className="vb-method"><div><p className="vb-eyebrow">How MVPI thinks</p><h2>Who you played matters.<br />How competitive you were matters too.</h2></div><p>Opponent-adjusted set performance contributes 35%, MVPI opponent strength 15%, record 10%, set percentage 10%, recent form 5%, media statewide rank 15%, and media schedule strength 10%. Enrollment class is only a fading early-season prior.</p></section>
      <footer><span>MVPI · Mississippi Volleyball Power Index</span><span>Media records and results · MHSAA 1A–7A classifications</span></footer>
    </main>
  );
}
