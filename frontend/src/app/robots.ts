import { MetadataRoute } from 'next'
import { getConfiguredAppOrigin } from '@/lib/url'

export default function robots(): MetadataRoute.Robots {
    const appOrigin = getConfiguredAppOrigin()

    return {
        rules: {
            userAgent: '*',
            allow: '/',
            disallow: ['/api/', '/admin/', '/private/'],
        },
        sitemap: `${appOrigin}/sitemap.xml`,
    }
}
