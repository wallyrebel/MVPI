import type { MetadataRoute } from 'next';
import snapshot from '../data/volleyball/current.json';
import { siteUrl } from './site';

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date(`${snapshot.metadata.generated_at}T12:00:00Z`);

  const staticPages: MetadataRoute.Sitemap = [
    { url: siteUrl, changeFrequency: 'daily', priority: 1, lastModified },
    { url: `${siteUrl}/teams`, changeFrequency: 'daily', priority: 0.7, lastModified },
    { url: `${siteUrl}/methodology`, changeFrequency: 'monthly', priority: 0.6, lastModified },
    { url: `${siteUrl}/about`, changeFrequency: 'monthly', priority: 0.5, lastModified },
    { url: `${siteUrl}/contact`, changeFrequency: 'yearly', priority: 0.3, lastModified },
    { url: `${siteUrl}/privacy`, changeFrequency: 'yearly', priority: 0.2, lastModified },
  ];

  const teamPages: MetadataRoute.Sitemap = snapshot.rankings.map((row) => ({
    url: `${siteUrl}/team/${row.team_id}`,
    changeFrequency: 'daily' as const,
    priority: 0.8,
    lastModified,
  }));

  return [...staticPages, ...teamPages];
}
