import { Metadata } from "next"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Logo } from "@/components/logo"
import {
  Search,
  Briefcase,
  Mail,
  TrendingUp,
  Zap,
  Shield,
  Users,
  CheckCircle,
  ArrowRight,
  Star,
  Clock,
  Target
} from "lucide-react"
import Link from "next/link"
import { LandingPageCTA } from "@/components/landing-page-cta"

export const metadata: Metadata = {
  title: "JobFlow Pro - AI-Powered Job Search Automation Platform | Resume Evaluation & LinkedIn Integration",
  description: "Transform your job search with AI-powered automation. Extract jobs from LinkedIn URLs, evaluate resumes with 100-point scoring, track applications via Gmail integration, and get smart job matching. Perfect for students, graduates, and job seekers.",
  keywords: "LinkedIn job automation, AI resume evaluation, job search automation, LinkedIn job extraction, Gmail job tracking, AI job matching, resume scoring, application tracking, career automation, job search platform, ATS optimization, interview preparation",
  openGraph: {
    title: "JobFlow Pro - Complete AI Job Search Automation Platform",
    description: "AI-powered job search automation with resume evaluation, LinkedIn integration, and Gmail tracking. Land your dream job faster with smart automation.",
    type: "website",
    url: "https://jobflowpro.com",
    images: [
      {
        url: "https://jobflowpro.com/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "JobFlow Pro - AI Job Search Automation Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "JobFlow Pro - AI Job Search Automation Platform",
    description: "AI-powered job search with resume evaluation, LinkedIn integration, and Gmail tracking.",
    images: ["https://jobflowpro.com/og-image.jpg"],
  },
  robots: "index, follow",
  alternates: {
    canonical: "https://jobflowpro.com",
  },
  authors: [{ name: "JobFlow Pro Team" }],
  creator: "JobFlow Pro",
  publisher: "JobFlow Pro",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
}

const features = [
  {
    icon: Search,
    title: "Smart Job Extraction",
    description: "Extract complete job details from LinkedIn, Indeed, and other job board URLs with one click. Get company info, salary, requirements, and more automatically."
  },
  {
    icon: Target,
    title: "AI Resume Evaluation",
    description: "Get comprehensive resume analysis with 100-point scoring system. ATS optimization, keyword analysis, and personalized improvement suggestions."
  },
  {
    icon: Mail,
    title: "Gmail Integration",
    description: "Automatically track job application emails, interview invitations, and responses. Never miss important communications from employers."
  },
  {
    icon: Briefcase,
    title: "Application Management",
    description: "Track all applications with detailed status updates, notes, and follow-up reminders. Monitor your success rate and application pipeline."
  },
  {
    icon: TrendingUp,
    title: "AI Job Matching",
    description: "Get smart job recommendations based on your skills, experience, and preferences. Compatibility scoring helps you find the best opportunities."
  },
  {
    icon: Users,
    title: "Analytics Dashboard",
    description: "Comprehensive insights into your job search performance. Track application rates, response rates, and optimize your strategy."
  }
]

const benefits = [
  "Save 15+ hours per week on job searching and application tracking",
  "Get AI-powered resume feedback with 100-point scoring system",
  "Never miss interview invitations or important email responses",
  "Track application success rates with detailed analytics",
  "Extract job details from any URL in seconds, not minutes",
  "Get smart job matches based on your actual skills and experience",
  "Optimize your resume for ATS systems automatically",
  "Monitor your entire job search pipeline in one dashboard"
]

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Software Engineer at Google",
    content: "The resume evaluation feature helped me improve my ATS score from 65 to 92. Combined with the job extraction, I saved 20+ hours per week on applications.",
    rating: 5
  },
  {
    name: "Marcus Rodriguez",
    role: "Product Manager at Microsoft",
    content: "The Gmail integration is a game-changer. I never miss interview invitations anymore, and the AI job matching helped me find roles I wouldn't have considered.",
    rating: 5
  },
  {
    name: "Emily Watson",
    role: "Marketing Coordinator at Shopify",
    content: "As a recent graduate, this platform gave me the confidence to apply strategically. The analytics showed me exactly where to improve my applications.",
    rating: 5
  }
]

export default function LandingPage() {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "JobFlow Pro",
    "description": "AI-powered job search automation platform with resume evaluation, LinkedIn integration, and Gmail tracking",
    "url": "https://jobflowpro.com",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD",
      "description": "Free for students"
    },
    "featureList": [
      "Smart Job Extraction from LinkedIn and job boards",
      "AI Resume Evaluation with 100-point scoring",
      "Gmail Integration for application tracking",
      "AI Job Matching and compatibility scoring",
      "Application Management Dashboard",
      "Analytics and Performance Insights"
    ],
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.9",
      "ratingCount": "1200"
    }
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <Logo size={40} href="/" />
            <div className="flex items-center space-x-4">
              <Link href="#features">
                <Button variant="ghost">Features</Button>
              </Link>
              {/* Removed duplicate button - only LandingPageCTA will handle authentication */}
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="container mx-auto px-4 py-20">
          <div className="text-center max-w-4xl mx-auto">
            <Badge className="mb-6 bg-secondary text-secondary-foreground hover:bg-secondary/80">
              🚀 AI-Powered Job Search Automation
            </Badge>
            <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6 leading-tight">
              Land Your Dream Job with
              <span className="text-primary"> Complete AI Automation</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              The only platform that combines job extraction, resume evaluation, Gmail tracking, and AI matching.
              Transform your job search from hours of manual work to minutes of smart automation.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <LandingPageCTA size="lg" />
              <Button variant="outline" size="lg" className="text-lg px-8 py-3">
                Watch Demo
              </Button>
            </div>
            <div className="mt-8 flex items-center justify-center space-x-8 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Free for students</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Setup in 2 minutes</span>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="container mx-auto px-4 py-16">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">2,500+</div>
              <div className="text-muted-foreground">Jobs Extracted</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">85%</div>
              <div className="text-muted-foreground">Time Saved</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">500+</div>
              <div className="text-muted-foreground">Resumes Evaluated</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">1,200+</div>
              <div className="text-muted-foreground">Users Helped</div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="container mx-auto px-4 py-20">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">
              Everything You Need to Ace Your Job Search
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              From job extraction to application tracking, we've got every aspect of your job search covered.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-primary-foreground" />
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-muted-foreground">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Benefits Section */}
        <section className="bg-secondary py-20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-foreground mb-4">
                Why Students Choose JobFlow Pro
              </h2>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Join thousands of students who have transformed their job search experience.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-start space-x-4">
                  <CheckCircle className="w-6 h-6 text-primary mt-1 flex-shrink-0" />
                  <span className="text-foreground text-lg">{benefit}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="container mx-auto px-4 py-20">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">
              How It Works
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Get started in minutes with our simple 3-step process.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-primary-foreground">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Connect & Upload</h3>
              <p className="text-muted-foreground">
                Sign in with Google for Gmail integration, then upload your resume for AI-powered evaluation and optimization suggestions.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-primary-foreground">2</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Extract & Analyze</h3>
              <p className="text-muted-foreground">
                Extract job details from any LinkedIn or job board URL. Get AI-powered job matching scores and compatibility analysis.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-primary-foreground">3</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Track & Optimize</h3>
              <p className="text-muted-foreground">
                Monitor all applications with automated email tracking. Get insights and recommendations to improve your success rate.
              </p>
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section className="bg-secondary py-20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-foreground mb-4">
                What Students Are Saying
              </h2>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Join thousands of satisfied students who have transformed their job search.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {testimonials.map((testimonial, index) => (
                <Card key={index} className="border-0 shadow-lg">
                  <CardContent className="p-6">
                    <div className="flex items-center mb-4">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                      ))}
                    </div>
                    <p className="text-muted-foreground mb-4">"{testimonial.content}"</p>
                    <div>
                      <div className="font-semibold text-foreground">{testimonial.name}</div>
                      <div className="text-sm text-muted-foreground">{testimonial.role}</div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="container mx-auto px-4 py-20">
          <div className="text-center max-w-3xl mx-auto">
            <h2 className="text-4xl font-bold text-foreground mb-4">
              Ready to Land Your Dream Job 3x Faster?
            </h2>
            <p className="text-xl text-muted-foreground mb-8">
              Join 1,200+ job seekers who have transformed their job search with AI-powered automation.
              Get resume evaluation, job extraction, and email tracking all in one platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <LandingPageCTA size="lg" />
              <Button variant="outline" size="lg" className="text-lg px-8 py-3">
                View Demo
              </Button>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              No credit card required • Free for students • Setup in 2 minutes • 30-day money-back guarantee
            </p>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-primary text-primary-foreground py-12">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div>
                <div className="mb-4">
                  <Logo size={32} />
                </div>
                <p className="text-primary-foreground/80">
                  Complete AI-powered job search platform with resume evaluation, LinkedIn integration, and Gmail tracking for job seekers of all levels.
                </p>
              </div>
              <div>
                <h3 className="font-semibold mb-4">Product</h3>
                <ul className="space-y-2 text-primary-foreground/80">
                  <li><a href="#features" className="hover:text-primary-foreground">Features</a></li>
                  <li><a href="#features" className="hover:text-primary-foreground">How It Works</a></li>
                  <li><a href="#features" className="hover:text-primary-foreground">Pricing</a></li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-4">Support</h3>
                <ul className="space-y-2 text-primary-foreground/80">
                  <li><a href="#" className="hover:text-primary-foreground">Help Center</a></li>
                  <li><a href="#" className="hover:text-primary-foreground">Contact Us</a></li>
                  <li><a href="#" className="hover:text-primary-foreground">Documentation</a></li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-4">Company</h3>
                <ul className="space-y-2 text-primary-foreground/80">
                  <li><a href="#" className="hover:text-primary-foreground">About</a></li>
                  <li><a href="#" className="hover:text-primary-foreground">Privacy</a></li>
                  <li><a href="#" className="hover:text-primary-foreground">Terms</a></li>
                </ul>
              </div>
            </div>
            <div className="border-t border-primary-foreground/20 mt-8 pt-8 text-center text-primary-foreground/80">
              <p>&copy; 2024 JobFlow Pro. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}