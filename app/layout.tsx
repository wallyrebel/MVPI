import type { Metadata } from 'next';
import './globals.css';
import { siteUrl } from './site';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'Mississippi Volleyball Power Index | Mississippi Volleyball Rankings',
    template: '%s | Mississippi Volleyball Power Index',
  },
  description: 'Mississippi high school volleyball rankings using records, set scores, strength of schedule, opponent quality, and statewide rankings.',
  category: 'Sports',
  authors: [{ name: 'Mississippi Volleyball Power Index' }],
  creator: 'Mississippi Volleyball Power Index',
  publisher: 'Mississippi Volleyball Power Index',
  keywords: [
    'Mississippi Volleyball Power Index',
    'Mississippi volleyball rankings',
    'Mississippi high school volleyball rankings',
    'MHSAA volleyball rankings',
    'Mississippi volleyball scores',
    'Mississippi volleyball strength of schedule',
  ],
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    url: siteUrl,
    siteName: 'Mississippi Volleyball Power Index',
    title: 'Mississippi Volleyball Power Index | Mississippi Volleyball Rankings',
    description: 'Mississippi high school volleyball rankings using records, set scores, strength of schedule, opponent quality, and statewide rankings.',
    images: [{ url: '/og.png', width: 1734, height: 907, alt: 'Mississippi Volleyball Power Index' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Mississippi Volleyball Power Index | Mississippi Volleyball Rankings',
    description: 'Mississippi high school volleyball rankings with match results, set differential, and strength of schedule.',
    images: ['/og.png'],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
