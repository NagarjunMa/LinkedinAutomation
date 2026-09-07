import { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'PrismPro — Career Evidence Coach in Development',
    short_name: 'PrismPro',
    description: 'A career-evidence coach in development for truthful, role-aligned resumes, LinkedIn recommendations, and interview stories.',
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
