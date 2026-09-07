import { MetadataRoute } from 'next'
import { getConfiguredAppOrigin } from '@/lib/url'

export default function robots(): MetadataRoute.Robots {
    const appOrigin = getConfiguredAppOrigin()

    return {
        rules: {
            userAgent: '*',
            allow: ['/', '/privacy-policy', '/terms'],
            disallow: [
                '/api/',
                '/admin/',
                '/private/',
                '/login',
                '/onboarding',
                '/dashboard',
                '/docs',
            ],
        },
        sitemap: `${appOrigin}/sitemap.xml`,
    }
}
