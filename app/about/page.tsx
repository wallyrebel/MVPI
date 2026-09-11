import type { Metadata } from 'next';
import Link from 'next/link';
import { SiteFooter, SiteHeader } from '../site-nav';
import { generatedAt, longDate, rankings } from '../team-data';

export const metadata: Metadata = {
  title: 'About the Mississippi Volleyball Power Index',
  description: 'Who publishes MVPI, what the rating is, where the data comes from, and how often it updates.',
  alternates: { canonical: '/about' },
};

export default function AboutPage() {
  return (
    <main className="vb-main">
      <SiteHeader />
      <article className="vb-doc">
        <p className="vb-eyebrow">About</p>
        <h1>About MVPI</h1>
        <p className="vb-doc-meta">Rankings last updated {longDate(generatedAt)}</p>

        <p>
          The Mississippi Volleyball Power Index is an independent computer rating of high school volleyball teams in
          Mississippi. It currently rates {rankings.length} teams across MHSAA Classes 1A through 7A, Mississippi MAIS
          programs, and Northpoint Christian in Southaven.
        </p>

        <h2>What MVPI is</h2>
        <p>
          Win-loss record alone does not say much in a state where schedules differ enormously. A 20–5 team that played
          a statewide tournament schedule and a 20–5 team that played only its region are not the same team. MVPI exists
          to put every program on one scale by weighing not just whether a team won, but who it played and how
          competitive each set was.
        </p>
        <p>
          The result is a single number from roughly 1 to 100. It is a rating, not a prediction or a poll, and it has no
          official standing with any athletic association. It is one more piece of information for coaches, players,
          parents and fans who follow Mississippi volleyball.
        </p>

        <h2>What MVPI is not</h2>
        <ul>
          <li>It is not an official MHSAA, MAIS or TSSAA product, and carries no postseason seeding weight.</li>
          <li>It is not a human poll. No votes, no ballots, no preseason expectations.</li>
          <li>It does not rate teams with no published current-season results.</li>
        </ul>

        <h2>Where the data comes from</h2>
        <p>
          Team lists, classifications, records, schedules and match results come from published media schedules and
          statewide rankings feeds. Official association score data is used only to fill in a match the media feed does
          not list — it never overrides the published media record. Out-of-state opponents are rated using national
          media computer ratings converted onto the MVPI scale, so a Mississippi team gets fair credit for playing a
          strong team from Alabama, Tennessee, Arkansas or Louisiana.
        </p>
        <p>
          Every team page shows its own source data: the full schedule, each set score, and the rating of each opponent
          played. If something looks wrong, the underlying match list is right there to check.
        </p>

        <h2>How often it updates</h2>
        <p>
          Results are pulled and the ratings recalculated three times a week during the season — Tuesday, Friday and
          Sunday. The update date shown on the rankings page and on every team page reflects the most recent completed
          run.
        </p>

        <h2>Corrections</h2>
        <p>
          Published high school results contain errors, and MVPI inherits them. If you find a wrong score, a missing
          match, or a team in the wrong classification, send the detail and a source and it will be checked against the
          next run. Corrections are welcome from anyone — coaches, scorekeepers, parents or fans.
        </p>
        <p>
          Write to <a href="mailto:editor@sportsmississippi.com">editor@sportsmississippi.com</a>, or see the{' '}
          <Link href="/contact">contact page</Link>. The full calculation is documented on the{' '}
          <Link href="/methodology">methodology page</Link>.
        </p>

        <h2>Who publishes it</h2>
        <p>
          MVPI is published by the Mississippi Volleyball Power Index, an independent Mississippi sports analytics
          project. It is funded by advertising and is free to read, with no paywall, subscription or account required.
        </p>
      </article>
      <SiteFooter />
    </main>
  );
}
