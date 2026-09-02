import type { MetadataRoute } from 'next';
import snapshot from '../data/volleyball/current.json';
import { siteUrl } from './site';

export default function sitemap(): MetadataRoute.Sitemap {
  return [{
    url: siteUrl,
    changeFrequency: 'daily',
    priority: 1,
    lastModified: new Date(`${snapshot.metadata.generated_at}T12:00:00Z`),
  }];
}
