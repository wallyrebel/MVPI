import Link from 'next/link';

export function SiteHeader() {
  return (
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
        <Link href="/contact">Contact</Link>
      </nav>
    </header>
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
        <Link href="/contact">Contact</Link>
        <Link href="/privacy">Privacy</Link>
      </nav>
    </footer>
  );
}
