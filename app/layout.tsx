import type { Metadata } from 'next';
import './globals.css';
import { siteUrl } from './site';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'Mississippi Volleyball Rankings & Power Index | MVPI',
    template: '%s | Mississippi Volleyball Power Index',
  },
  description: 'Mississippi volleyball rankings for MHSAA 1A–7A teams, MAIS schools and Northpoint Christian, using records, set scores and strength of schedule.',
  applicationName: 'Mississippi Volleyball Power Index',
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
    title: 'Mississippi Volleyball Rankings & Power Index | MVPI',
    description: 'Mississippi volleyball rankings for MHSAA 1A–7A teams, MAIS schools and Northpoint Christian, using records, set scores and strength of schedule.',
    images: [{ url: '/og.png', width: 1734, height: 907, alt: 'Mississippi Volleyball Power Index' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Mississippi Volleyball Rankings & Power Index | MVPI',
    description: 'Mississippi high school volleyball rankings for MHSAA classes and a combined Private group, powered by results, set scores and strength of schedule.',
    images: ['/og.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
      'max-video-preview': -1,
    },
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
