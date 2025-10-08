import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase-server'

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url)
        const code = searchParams.get('code')
        const state = searchParams.get('state')
        const error = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')

        // Handle OAuth errors
        if (error) {
            console.error('OAuth error:', error, errorDescription)
            return NextResponse.redirect(
                new URL(`/?error=${encodeURIComponent(errorDescription || error)}`, request.url)
            )
        }

        // Validate required parameters
        if (!code) {
            console.error('No authorization code received')
            return NextResponse.redirect(
                new URL('/?error=No authorization code received', request.url)
            )
        }

        // Create Supabase server client
        const supabase = createServerSupabaseClient()

        try {
            // Exchange code for session
            const { data, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)

            if (exchangeError) {
                console.error('Error exchanging code for session:', exchangeError)
                return NextResponse.redirect(
                    new URL(`/?error=${encodeURIComponent(exchangeError.message)}`, request.url)
                )
            }

            if (!data.session) {
                console.error('No session received after code exchange')
                return NextResponse.redirect(
                    new URL('/?error=No session received after authentication', request.url)
                )
            }

            // Check if this is a new user or existing user
            const { data: { user }, error: userError } = await supabase.auth.getUser()

            if (userError) {
                console.error('Error getting user:', userError)
                return NextResponse.redirect(
                    new URL('/?error=Failed to get user information', request.url)
                )
            }

            console.log('Auth callback: User email:', user?.email, 'User ID:', user?.id)

            // Check if user has completed onboarding (has profile data)
            const isNewUser = !user?.user_metadata?.onboarding_completed
            const isFirstTimeOAuth = !user?.user_metadata?.oauth_provider

            console.log('Auth callback: Is new user:', isNewUser, 'Is first time OAuth:', isFirstTimeOAuth)

            // Successfully authenticated - redirect based on user status
            let redirectUrl = '/dashboard'

            if (isNewUser && isFirstTimeOAuth) {
                // For completely new users, redirect to onboarding
                redirectUrl = '/onboarding'
                console.log('Auth callback: Redirecting new user to onboarding')
            } else {
                // For existing users or users who have completed onboarding, go to dashboard
                console.log('Auth callback: Redirecting existing user to dashboard')
            }

            const response = NextResponse.redirect(new URL(redirectUrl, request.url))

            // Set authentication cookies
            const { access_token, refresh_token } = data.session

            if (access_token) {
                response.cookies.set('sb-access-token', access_token, {
                    httpOnly: true,
                    secure: process.env.NODE_ENV === 'production',
                    sameSite: 'lax',
                    maxAge: 60 * 60 * 24 * 7, // 7 days
                    path: '/'
                })
            }

            if (refresh_token) {
                response.cookies.set('sb-refresh-token', refresh_token, {
                    httpOnly: true,
                    secure: process.env.NODE_ENV === 'production',
                    sameSite: 'lax',
                    maxAge: 60 * 60 * 24 * 30, // 30 days
                    path: '/'
                })
            }

            return response

        } catch (sessionError) {
            console.error('Session establishment error:', sessionError)
            return NextResponse.redirect(
                new URL('/?error=Failed to establish session', request.url)
            )
        }

    } catch (error) {
        console.error('Unexpected error in auth callback:', error)
        return NextResponse.redirect(
            new URL('/?error=An unexpected error occurred during authentication', request.url)
        )
    }
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { code } = body

        if (!code) {
            return NextResponse.json(
                { error: 'Authorization code is required' },
                { status: 400 }
            )
        }

        // Create Supabase server client
        const supabase = createServerSupabaseClient()

        // Exchange code for session
        const { data, error } = await supabase.auth.exchangeCodeForSession(code)

        if (error) {
            console.error('Error exchanging code for session:', error)
            return NextResponse.json(
                { error: error.message },
                { status: 400 }
            )
        }

        if (!data.session) {
            return NextResponse.json(
                { error: 'No session received after authentication' },
                { status: 400 }
            )
        }

        // Return session data for client-side handling
        return NextResponse.json({
            success: true,
            session: {
                access_token: data.session.access_token,
                refresh_token: data.session.refresh_token,
                user: data.session.user
            }
        })

    } catch (error) {
        console.error('Unexpected error in auth callback POST:', error)
        return NextResponse.json(
            { error: 'An unexpected error occurred during authentication' },
            { status: 500 }
        )
    }
}
