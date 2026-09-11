import type { Metadata } from 'next';
import Link from 'next/link';
import { SiteFooter, SiteHeader } from '../site-nav';
import { classPeers, generatedAt, longDate, rankings } from '../team-data';

export const metadata: Metadata = {
  title: 'All Mississippi Volleyball Teams',
  description: 'Every ranked Mississippi high school volleyball team by MHSAA class and the Private group, with record and MVPI rating. Links to each team page.',
  alternates: { canonical: '/teams' },
};

const GROUPS = ['7A', '6A', '5A', '4A', '3A', '2A', '1A', 'Private'] as const;

export default function TeamsIndexPage() {
  return (
    <main className="vb-main">
      <SiteHeader />
      <article className="vb-doc vb-doc-wide">
        <p className="vb-eyebrow">Team directory</p>
        <h1>All ranked teams</h1>
        <p className="vb-doc-meta">
          {rankings.length} teams · updated {longDate(generatedAt)}
        </p>
        <p>
          Every team MVPI currently rates, grouped by MHSAA classification plus the Private group. Each team page
          carries its full 2026 schedule, set scores, opponent ratings and a breakdown of how its rating is built.
        </p>
      </article>

      {GROUPS.map((group) => {
        const teams = classPeers(group);
        if (teams.length === 0) return null;
        return (
          <section className="vb-directory" key={group} id={group}>
            <h2>{group === 'Private' ? 'Private' : `Class ${group}`} <small>{teams.length} teams</small></h2>
            <div>
              {teams.map((row, index) => (
                <Link key={row.team_id} href={`/team/${row.team_id}`}>
                  <span className="vb-dir-rank tabular">{index + 1}</span>
                  <span className="vb-dir-name">{row.team}</span>
                  <span className="vb-dir-meta tabular">{row.record} · {row.mvpi.toFixed(1)}</span>
                </Link>
              ))}
            </div>
          </section>
        );
      })}

      <SiteFooter />
    </main>
  );
}
