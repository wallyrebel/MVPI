import type { Metadata } from 'next';
import Link from 'next/link';
import { SiteFooter, SiteHeader } from '../site-nav';

export const metadata: Metadata = {
  title: 'Contact',
  description: 'Reach the Mississippi Volleyball Power Index with a score correction, a missing match, or a question about the rating.',
  alternates: { canonical: '/contact' },
};

const CONTACT = 'editor@sportsmississippi.com';

export default function ContactPage() {
  return (
    <main className="vb-main">
      <SiteHeader />
      <article className="vb-doc">
        <p className="vb-eyebrow">Contact</p>
        <h1>Contact MVPI</h1>

        <p>
          Email <a href={`mailto:${CONTACT}`}>{CONTACT}</a>. Messages are read by the person who maintains the rankings,
          and corrections are usually reflected in the next scheduled run.
        </p>

        <h2>Reporting a wrong or missing result</h2>
        <p>
          This is the most useful thing you can send. Published high school results are frequently incomplete, and a
          single missing tournament match can move a team several places. To make a correction quick to verify, include:
        </p>
        <ul>
          <li>Both team names, as they appear on the rankings page</li>
          <li>The date of the match</li>
          <li>The set score, or at least the match result</li>
          <li>A link or source, if you have one — a schedule page, bracket or box score</li>
        </ul>
        <p>
          Corrections are checked against the source feed rather than entered by hand, so a result that has not been
          published anywhere may not be fixable until it is.
        </p>

        <h2>Other questions</h2>
        <ul>
          <li>
            <strong>Why is my team not ranked?</strong> Teams without published current-season results, or without a
            published statewide ranking, stay unranked. See the{' '}
            <Link href="/methodology">methodology page</Link>.
          </li>
          <li>
            <strong>Why is my team rated below a team we beat?</strong> Head-to-head is one input among several. The
            rating breakdown on each team page shows exactly which components are carrying the number.
          </li>
          <li>
            <strong>Media and reuse.</strong> You are welcome to cite MVPI ratings with attribution and a link. Get in
            touch for anything more involved.
          </li>
          <li>
            <strong>Advertising and privacy.</strong> See the <Link href="/privacy">privacy policy</Link>.
          </li>
        </ul>

        <h2>What this site is</h2>
        <p>
          MVPI is an independent project, not an official product of the MHSAA, MAIS, TSSAA, or any school. More detail
          is on the <Link href="/about">about page</Link>.
        </p>
      </article>
      <SiteFooter />
    </main>
  );
}
