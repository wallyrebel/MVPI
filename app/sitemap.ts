import type { MetadataRoute } from 'next';
import { siteUrl } from './site';

export default function sitemap(): MetadataRoute.Sitemap {
  return [{
    url: siteUrl,
    changeFrequency: 'daily',
    priority: 1,
  }];
}
