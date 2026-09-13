import Link from 'next/link';
import { adEmail, adMailto } from './site';

/** Top-of-page advertising CTA. Rendered by SiteHeader, so it is on every page. */
export function AdvertiseBanner() {
  return (
    <aside className="vb-adbar">
      <p>
        <b>Advertise on MVPI</b>
        <strong>Reach Mississippi volleyball coaches, players and families.</strong>{' '}
        <span className="vb-adbar-sub">Statewide rankings, every class, updated three times a week all season.</span>
      </p>
      <div>
        <Link className="vb-adbar-cta" href="/advertise">Advertise with us</Link>
        <a className="vb-adbar-mail" href={adMailto}>{adEmail}</a>
      </div>
    </aside>
  );
}

export function SiteHeader() {
  return (
    <>
      <AdvertiseBanner />
      <header className="vb-header">
        <Link className="vb-brand" href="/">
          <span>V</span>
          <div><strong>Mississippi Volleyball</strong><small>POWER INDEX</small></div>
        </Link>
        <nav className="vb-nav" aria-label="Site">
          <Link href="/">Rankings</Link>
          <Link href="/teams">Teams</Link>
          <Link href="/methodology">Methodology</Link>
          <Link href="/about">About</Link>
          <Link href="/advertise">Advertise</Link>
          <Link href="/contact">Contact</Link>
        </nav>
      </header>
    </>
  );
}

export function SiteFooter() {
  return (
    <footer className="vb-footer">
      <div>
        <strong>MVPI · Mississippi Volleyball Power Index</strong>
        <span>Media records and results · MHSAA 1A–7A · MAIS · Northpoint Christian</span>
      </div>
      <nav aria-label="Footer">
        <Link href="/">Rankings</Link>
        <Link href="/teams">Teams</Link>
        <Link href="/methodology">Methodology</Link>
        <Link href="/about">About</Link>
        <Link href="/advertise">Advertise</Link>
        <Link href="/contact">Contact</Link>
        <Link href="/privacy">Privacy</Link>
      </nav>
    </footer>
  );
}
