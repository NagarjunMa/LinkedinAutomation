import { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Prism Pro — Recruiter-Grade Resume Prep',
    short_name: 'Prism Pro',
    description: 'Recruiter-grade resume tailoring, JD matching, and ATS-ready PDF export for experienced engineers and product professionals.',
    start_url: '/',
    display: 'standalone',
    background_color: '#ece9e3',
    theme_color: '#1a1a1a',
    icons: [
      {
        src: '/favicon.ico',
        sizes: 'any',
        type: 'image/x-icon',
      },
    ],
  }
}
