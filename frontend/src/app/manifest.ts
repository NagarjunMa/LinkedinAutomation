import { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Prism Pro — Recruiter-Grade Resume Prep',
    short_name: 'Prism Pro',
    description: 'Recruiter-grade resume tailoring, JD matching, and ATS-ready PDF export for experienced engineers and product professionals.',
    start_url: '/',
    display: 'standalone',
    background_color: '#f7f5f2',
    theme_color: '#b85a3a',
    icons: [
      {
        src: '/icon-192.png',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        src: '/icon-512.png',
        sizes: '512x512',
        type: 'image/png',
      },
    ],
  }
}
