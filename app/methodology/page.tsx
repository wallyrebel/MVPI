import type { Metadata } from 'next';
import Link from 'next/link';
import { SiteFooter, SiteHeader } from '../site-nav';
import { generatedAt, longDate, rankings } from '../team-data';

export const metadata: Metadata = {
  title: 'MVPI Methodology',
  description: 'How the Mississippi Volleyball Power Index is calculated: component weights, percentile scaling, opponent adjustment and out-of-state ratings.',
  alternates: { canonical: '/methodology' },
};

const WEIGHTS: Array<[string, string, string]> = [
  ['35%', 'Opponent-adjusted set performance', 'Per-set margin adjusted for the quality of the opponent faced. Beating a strong team in four sets can rate higher than sweeping a weak one.'],
  ['15%', 'MVPI opponent strength', 'The average MVPI rating of every opponent a team has actually played. This is a rating average, not opponent win percentage.'],
  ['15%', 'Media statewide rank', 'The published statewide ordinal rank, converted to a higher-is-better percentile.'],
  ['10%', 'Record', 'Win percentage taken from the authoritative published media record.'],
  ['10%', 'Set percentage', 'Share of all sets won across every published match score.'],
  ['10%', 'Media schedule strength', 'The published strength-of-schedule field from the statewide feed.'],
  ['5%', 'Recent form', 'Opponent-adjusted performance across the last five matches.'],
];

export default function MethodologyPage() {
  return (
    <main className="vb-main">
      <SiteHeader />
      <article className="vb-doc">
        <p className="vb-eyebrow">Methodology · Formula MVPI 0.3</p>
        <h1>How MVPI is calculated</h1>
        <p className="vb-doc-meta">
          Current run {longDate(generatedAt)} · {rankings.length} ranked teams
        </p>

        <p>
          MVPI answers one question: based on whom a team has played and how it performed, how strong is that team right
          now? Everything below is computed from published results. There are no votes and no preseason expectations.
        </p>

        <h2>The seven components</h2>
        <p>
          Each component is first computed as a raw value, then converted to a <strong>statewide percentile</strong>
          {' '}among ranked teams, then weighted. Percentile scaling is what lets a set-margin number and a
          strength-of-schedule number be added together meaningfully. The weighted sum is scaled to roughly 1–100 and
          displayed to one decimal, while ordering uses full precision.
        </p>
        <table className="vb-weights-table">
          <thead>
            <tr><th>Weight</th><th>Component</th><th>What it measures</th></tr>
          </thead>
          <tbody>
            {WEIGHTS.map(([weight, name, note]) => (
              <tr key={name}><td className="tabular">{weight}</td><td>{name}</td><td>{note}</td></tr>
            ))}
          </tbody>
        </table>

        <h2>Opponent adjustment</h2>
        <p>
          The largest single input is opponent-adjusted set performance. Rather than asking only whether a team won,
          MVPI asks how it performed per set relative to the rating of the team across the net. Opponent ratings and
          team ratings are solved together and iterated until they stop moving, so the whole state settles into one
          connected picture rather than a set of isolated records.
        </p>
        <p>
          This is why a team can lose and still gain ground, and why an undefeated team with a thin schedule does not
          automatically sit at No. 1.
        </p>

        <h2>Classification and the Private group</h2>
        <p>
          Every team is rated on the same statewide scale. Class lists are filtered views of that one calculation — a
          class rating is never recomputed separately. MHSAA enrollment class acts only as a fading early-season
          assumption while few results exist, and real results progressively replace it.
        </p>
        <p>
          Private is a display group covering Mississippi MAIS schools plus Northpoint Christian, which plays in the
          TSSAA. It is a grouping for readability, not an official association class.
        </p>

        <h2>Out-of-state opponents</h2>
        <p>
          When a Mississippi team plays a team from another state, that opponent has no MVPI rating of its own. MVPI
          uses national media computer ratings, converted onto the MVPI scale, so the game still carries appropriate
          opponent credit. Where no rating is available, the opponent starts from a neutral estimate and its results
          shape the rating from there. The rankings page lists any opponent whose rating could not be retrieved.
        </p>

        <h2>Records and set data</h2>
        <p>
          The published media record is authoritative. Where a team&rsquo;s schedule feed lists more completed matches than
          the statewide snapshot — which happens with tournaments — the fuller list is used, but results are never
          invented. Some matches are published with a result but no set-by-set score; those still count toward the
          record, and each team page shows how many of its matches have usable set data.
        </p>

        <h2>Who gets ranked</h2>
        <p>
          A team needs published current-season results to be rated. Schools with no published results, or no published
          statewide ranking, remain unranked until that data appears.
        </p>

        <h2>Update schedule</h2>
        <p>
          Data is pulled and ratings recalculated three times a week in season — Tuesday, Friday and Sunday. Every team
          page and the sitemap carry the date of the most recent completed run.
        </p>

        <p>
          See the <Link href="/">full rankings</Link>, or read more <Link href="/about">about the project</Link>.
        </p>
      </article>
      <SiteFooter />
    </main>
  );
}
