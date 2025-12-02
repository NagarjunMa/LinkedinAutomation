import { createClient } from './supabase'

/**
 * Alternative OAuth approach that bypasses potential PKCE issues
 * by using direct window navigation to Supabase OAuth URL
 */
export const signInWithGoogleAlternative = async () => {
  try {
    const supabase = createClient()

    // Get the OAuth URL without initiating the flow immediately
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/api/auth/callback`,
        skipBrowserRedirect: true, // We'll handle redirect manually
        queryParams: {
          access_type: 'offline',
          prompt: 'select_account',
          scope: 'email profile https://www.googleapis.com/auth/gmail.readonly'
        }
      }
    })

    if (error) {
      console.error('OAuth URL generation failed:', error)
      throw error
    }

    if (data.url) {
      console.log('🔄 Redirecting to OAuth URL:', data.url)
      // Manual redirect to ensure proper PKCE flow
      window.location.href = data.url
    } else {
      throw new Error('No OAuth URL generated')
    }

    return data
  } catch (error) {
    console.error('Alternative OAuth failed:', error)
    throw error
  }
}

/**
 * Debug function to check current OAuth state
 */
export const debugOAuthState = () => {
  const cookies = document.cookie.split(';').reduce((acc, cookie) => {
    const [name, value] = cookie.trim().split('=')
    if (name.includes('supabase') || name.includes('sb-') || name.includes('code_verifier')) {
      acc[name] = value
    }
    return acc
  }, {} as Record<string, string>)

  console.log('🍪 OAuth-related cookies:', cookies)
  return cookies
}