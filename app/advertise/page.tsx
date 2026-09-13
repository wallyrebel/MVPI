import type { Metadata } from 'next';
import Link from 'next/link';
import snapshot from '../../data/volleyball/current.json';
import { SiteFooter, SiteHeader } from '../site-nav';
import { adEmail, adMailto } from '../site';
import { generatedAt, longDate, rankings } from '../team-data';

export const metadata: Metadata = {
  title: 'Advertise with MVPI',
  description:
    'Reach Mississippi high school volleyball coaches, players, parents and fans. Display placements, team-page and class sponsorships on the Mississippi Volleyball Power Index.',
  alternates: { canonical: '/advertise' },
};

export default function AdvertisePage() {
  const matches = snapshot.metadata.completed_matches.toLocaleString('en-US');

  return (
    <main className="vb-main">
      <SiteHeader />
      <article className="vb-doc">
        <p className="vb-eyebrow">Advertise</p>
        <h1>Advertise with MVPI</h1>
        <p className="vb-doc-meta">Rankings last updated {longDate(generatedAt)}</p>

        <p>
          People do not land on a volleyball power index by accident. Everyone reading this site came looking for one
          thing: where Mississippi high school volleyball teams stand. That makes it a small, specific, local audience
          — and if you are trying to reach volleyball families in this state, it is a better place to spend an
          advertising dollar than a general-interest feed that happens to be seen by a few of them.
        </p>

        <ul className="vb-ad-stats">
          <li>
            <strong>{rankings.length}</strong>
            <small>Teams rated</small>
          </li>
          <li>
            <strong>{matches}</strong>
            <small>Matches tracked</small>
          </li>
          <li>
            <strong>3&times;</strong>
            <small>Updates per week</small>
          </li>
        </ul>

        <h2>Why advertise here</h2>
        <ul className="vb-ad-points">
          <li>
            <strong>The audience is already narrowed</strong>
            <small>
              Readers are coaches, players, parents, grandparents, athletic directors and fans following specific
              Mississippi programs. You are not paying for impressions from people three states away.
            </small>
          </li>
          <li>
            <strong>They come back all season</strong>
            <small>
              Ratings are recalculated three times a week — Tuesday, Friday and Sunday. Teams move. That is a reason to
              check again after every round of matches instead of reading once and leaving.
            </small>
          </li>
          <li>
            <strong>{rankings.length} team pages, not one homepage</strong>
            <small>
              Every ranked team has its own page with a full schedule, every set score and an opponent-by-opponent
              breakdown. A business can sit next to the schools its own town actually follows.
            </small>
          </li>
          <li>
            <strong>Statewide, every class</strong>
            <small>
              MHSAA Classes 1A through 7A, MAIS programs and Northpoint Christian. Small-town programs get the same
              coverage as the 7A schools, so a small-town advertiser is not an afterthought.
            </small>
          </li>
          <li>
            <strong>The page is not buried in ads</strong>
            <small>
              Ad load is kept light on purpose. Your message is not competing with a dozen other units, autoplay video
              and a pop-up for the same square inch.
            </small>
          </li>
          <li>
            <strong>Free to read, no paywall</strong>
            <small>
              No subscription, no login, no registration wall standing between a reader and your ad. Everything on the
              site is open.
            </small>
          </li>
        </ul>

        <h2>What is available</h2>
        <ul>
          <li>
            <strong>Run-of-site display.</strong> Top, in-content or footer placement across the rankings, team and
            directory pages.
          </li>
          <li>
            <strong>Team or class sponsorship.</strong> A &ldquo;presented by&rdquo; line on a single classification, or on
            the team pages for the schools you care about.
          </li>
          <li>
            <strong>Season-long presenting sponsorship</strong> of the main rankings page, from the first update of the
            season through the state tournament.
          </li>
          <li>
            <strong>Short postseason flights,</strong> for the weeks when readership concentrates around the playoffs.
          </li>
          <li>
            <strong>Plain text or logo placements</strong> for local businesses that do not have display creative ready
            to go.
          </li>
        </ul>
        <p>
          Length of run is flexible. A one-week flight for a local tournament and a sponsorship that runs from August
          through the championship are both fine.
        </p>

        <h2>Businesses that fit well</h2>
        <p>
          Anything a volleyball family in Mississippi already spends money on, and anything that travels with a team on
          a Saturday:
        </p>
        <ul>
          <li>Club volleyball programs, camps, clinics and private coaching</li>
          <li>Sports medicine, physical therapy, orthopedic and chiropractic clinics</li>
          <li>Orthodontists, dentists and optometrists</li>
          <li>Team photographers and videographers</li>
          <li>Spirit wear, screen printing and embroidery shops</li>
          <li>Restaurants, pizza places and caterers near a gym or along a travel route</li>
          <li>Banks, credit unions, insurance agents and car dealerships</li>
          <li>Colleges, junior colleges and recruiting or highlight-film services</li>
          <li>Tournaments, fundraisers and booster club events looking for attendance</li>
        </ul>

        <h2>Rates and traffic</h2>
        <p>
          Current traffic figures and a rate card go out by email on request. Tell me roughly what you are after and you
          will get the numbers that actually matter for it, rather than a deck. Rates are set for Mississippi businesses
          and booster clubs, not national media buyers, and there is room to build something small if that is what the
          budget is.
        </p>

        <h2>Advertising does not move the rankings</h2>
        <p>
          The rating is computed from published results by a documented formula, and the{' '}
          <Link href="/methodology">full methodology</Link> is public so anyone can check the math. Advertisers buy
          placement, not position. No sponsor has been moved up a spot and none will be — the worth of this site to a
          reader, and so its worth to you, depends entirely on that staying true.
        </p>

        <div className="vb-ad-cta">
          <h2>Get in touch</h2>
          <p>
            Email <a href={adMailto}>{adEmail}</a> and you will hear back from the person who runs the site, not a sales
            team. To get a useful answer in the first reply, include your business and where in the state you are, who
            you are trying to reach, the dates or season window you have in mind, whether you already have artwork, and
            a rough budget range if you have one.
          </p>
          <p>
            <a className="vb-ad-button" href={adMailto}>Email {adEmail}</a>
          </p>
        </div>

        <h2>About the site</h2>
        <p>
          MVPI is an independent Mississippi sports analytics project covering {rankings.length} volleyball teams across
          MHSAA Classes 1A through 7A, MAIS and Northpoint Christian. It is funded by advertising and free to read. More
          detail is on the <Link href="/about">about page</Link>, and general questions go to the{' '}
          <Link href="/contact">contact page</Link>.
        </p>
      </article>
      <SiteFooter />
    </main>
  );
}
