"use client"

import { useState, useEffect } from "react"
import { motion, useMotionValue, useTransform } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { Logo } from "@/components/logo"
import { cn } from "@/lib/utils"
import { useAuth } from "@/contexts/auth-context"
import { useRouter } from "next/navigation"
import { ThemeToggle } from "@/components/theme-toggle"
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
  Target,
  Upload,
  BookOpen,
  BarChart3,
  DollarSign,
  MapPin,
  ExternalLink,
  Play,
  RefreshCw,
  Award,
  Globe,
  Smartphone,
  ChevronDown,
  ChevronRight,
  X,
  Menu,
  ArrowUpRight,
  FileText,
  User,
  Calendar
} from "lucide-react"
import Link from "next/link"

// Animation variants
const fadeInVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.2 }
  }
}

const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
}

// Typewriter effect component
function TypewriterText({ text, speed = 100 }: { text: string; speed?: number }) {
  const [displayText, setDisplayText] = useState("")

  useEffect(() => {
    let i = 0
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayText(text.slice(0, i + 1))
        i++
      } else {
        clearInterval(timer)
      }
    }, speed)

    return () => clearInterval(timer)
  }, [text, speed])

  return <span>{displayText}</span>
}

// Count up animation component
function CountUpStat({ value, suffix = "" }: { value: number; suffix?: string }) {
  const count = useMotionValue(0)
  const rounded = useTransform(count, Math.round)
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    const animation = count.set(value)
    const unsubscribe = count.onChange(latest => setDisplayValue(Math.round(latest)))
    return unsubscribe
  }, [value, count])

  return <span>{displayValue}{suffix}</span>
}

// Main Navigation Component
function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const { user, signIn } = useAuth()
  const router = useRouter()

  const handleAuthAction = async () => {
    if (user) {
      // User is logged in, redirect to dashboard
      router.push('/dashboard')
    } else {
      // User is not logged in, sign in
      try {
        await signIn()
      } catch (error) {
        console.error('Sign in error:', error)
      }
    }
  }

  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 bg-primary-900/90 backdrop-blur-xl border-b border-primary-600"
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <Logo size={32} showText={false} />
            <span className="text-2xl font-neuton text-gradient-warm">JOBFLOW PRO</span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="#features" className="text-cream-200 hover:text-accent-400 transition-colors text-lg">Features</Link>
            <Link href="#pricing" className="text-cream-200 hover:text-accent-400 transition-colors text-lg">Pricing</Link>
            <Link href="#about" className="text-cream-200 hover:text-accent-400 transition-colors text-lg">About</Link>
          </div>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            <ThemeToggle />
            <Button
              variant="ghost"
              className="text-cream-200 hover:text-cream-50"
              onClick={handleAuthAction}
            >
              {user ? 'Dashboard' : 'Sign In'}
            </Button>
            <Button
              className="bg-gradient-warm hover:bg-gradient-gold text-white glow-orange hover:glow-gold transition-all duration-300"
              onClick={handleAuthAction}
            >
              {user ? 'Go to Dashboard' : 'Start Free'}
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="sm"
            className="md:hidden"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <motion.div
            className="md:hidden mt-4 py-4 border-t border-primary-600"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="flex flex-col space-y-4">
              <Link href="#features" className="text-cream-200 hover:text-accent-400 transition-colors text-lg">Features</Link>
              <Link href="#pricing" className="text-cream-200 hover:text-accent-400 transition-colors text-lg">Pricing</Link>
              <Link href="#about" className="text-cream-200 hover:text-accent-400 transition-colors text-lg">About</Link>
              <div className="flex flex-col space-y-2 pt-4 border-t border-primary-600">
                <div className="flex items-center justify-start mb-2">
                  <span className="text-cream-200 mr-3">Theme:</span>
                  <ThemeToggle />
                </div>
                <Button
                  variant="ghost"
                  className="text-cream-200 hover:text-cream-50 justify-start"
                  onClick={handleAuthAction}
                >
                  {user ? 'Dashboard' : 'Sign In'}
                </Button>
                <Button
                  className="bg-gradient-warm hover:bg-gradient-gold text-white"
                  onClick={handleAuthAction}
                >
                  {user ? 'Go to Dashboard' : 'Start Free'}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.nav>
  )
}

// Hero Section Component
function HeroSection() {
  const { user, signIn } = useAuth()
  const router = useRouter()

  const handleAuthAction = async () => {
    if (user) {
      router.push('/dashboard')
    } else {
      try {
        await signIn()
      } catch (error) {
        console.error('Sign in error:', error)
      }
    }
  }

  return (
    <section className="relative min-h-screen bg-primary-900 overflow-hidden flex items-center">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute top-20 left-20 w-96 h-96 bg-gradient-radial from-accent-500/20 to-transparent rounded-full blur-3xl"
          animate={{
            x: [0, 50, 0],
            y: [0, -30, 0],
          }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className="absolute bottom-20 right-20 w-96 h-96 bg-gradient-radial from-gold-500/20 to-transparent rounded-full blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, 30, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        />
      </div>

      <div className="max-w-7xl mx-auto px-6 py-20 pt-32 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Hero Content */}
          <motion.div
            className="space-y-8"
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
          >
            <motion.h1
              className="text-5xl lg:text-6xl xl:text-6xl 2xl:text-6xl font-neuton text-cream-50 leading-tight"
              variants={staggerItem}
            >
              <TypewriterText text="Stop Wasting Hours on Job Search Admin" speed={50} />
            </motion.h1>

            <motion.p
              className="text-2xl text-accent-400 font-semibold"
              variants={staggerItem}
            >
              AI-Powered Job Tracking • Expert Resume Evaluation • Automated Email Management
            </motion.p>

            <motion.p
              className="text-xl text-cream-200 leading-relaxed"
              variants={staggerItem}
            >
              JobFlow Pro helps students and new graduates save 15+ hours weekly with intelligent job analysis,
              recruiter-validated resume feedback, and automated application tracking.
            </motion.p>

            {/* Stats Row */}
            <motion.div
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
              variants={staggerItem}
            >
              <div className="text-center">
                <div className="text-2xl font-bold text-accent-400">
                  <CountUpStat value={15} suffix="+" />
                </div>
                <div className="text-base text-cream-300">Hours Saved Weekly</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gold-400">
                  <CountUpStat value={89} suffix="%" />
                </div>
                <div className="text-base text-cream-300">Student Satisfaction</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  <CountUpStat value={34} suffix="%" />
                </div>
                <div className="text-base text-cream-300">Higher Response Rates</div>
              </div>
            </motion.div>

            {/* CTA Buttons */}
            <motion.div
              className="flex flex-col sm:flex-row gap-4"
              variants={staggerItem}
            >
              <Button
                size="lg"
                className="bg-gradient-warm hover:bg-gradient-gold text-white text-lg px-8 py-4 glow-orange hover:glow-gold transition-all duration-300 hover:scale-105"
                onClick={handleAuthAction}
              >
                {user ? 'Go to Dashboard' : 'Start Free Trial'}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="border-accent-500 text-accent-400 hover:bg-accent-500/10 text-lg px-8 py-4"
              >
                <Play className="mr-2 h-5 w-5" />
                Watch Demo
              </Button>
            </motion.div>
          </motion.div>

          {/* Hero Visual */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 2.5 }}
          >
            <motion.div
              className="bg-gradient-card p-6 rounded-2xl border border-accent-500/20 glow-orange"
              animate={{
                y: [0, -20, 0],
              }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-cream-50">Dashboard Preview</h3>
                  <Badge className="bg-green-500">Live</Badge>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-primary-800 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-accent-400">
                      <CountUpStat value={42} />
                    </div>
                    <div className="text-sm text-cream-300">Applications</div>
                  </div>
                  <div className="bg-primary-800 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-gold-400">
                      <CountUpStat value={87} suffix="%" />
                    </div>
                    <div className="text-sm text-cream-300">ATS Score</div>
                  </div>
                </div>
                <Progress value={75} className="h-2" />
                <div className="text-sm text-cream-300">75% of weekly goal completed</div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

// Problem Section Component
function ProblemSection() {
  const problemCards = [
    {
      icon: Clock,
      title: "4-5 Hours Daily Wasted",
      description: "Copying job details, updating spreadsheets, and checking emails for responses eats up time you should spend on interview prep.",
      animation: "pulse"
    },
    {
      icon: BarChart3,
      title: "Lost in Application Chaos",
      description: "Tracking applications across LinkedIn, Indeed, and company sites with no centralized organization leads to missed opportunities.",
      animation: "shake"
    },
    {
      icon: Target,
      title: "Resume Uncertainty",
      description: "Wondering if your resume will pass ATS systems and attract recruiters. Generic AI tools don't provide recruiter-validated insights.",
      animation: "bounce"
    },
    {
      icon: Mail,
      title: "Email Management Nightmare",
      description: "Job responses buried in inbox alongside personal emails. Delayed follow-ups and missed interview invitations.",
      animation: "rotate"
    }
  ]

  return (
    <section id="problems" className="py-20 bg-primary-950">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          className="text-center mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeInVariants}
        >
          <h2 className="text-4xl font-neuton text-cream-50 mb-4">
            The Job Search Nightmare Students Face
          </h2>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-4 2xl:grid-cols-4 gap-6"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {problemCards.map((card, index) => (
            <motion.div key={index} variants={staggerItem}>
              <Card className="premium-card h-full hover:scale-105 transition-all duration-300">
                <CardContent className="p-6 text-center">
                  <motion.div
                    className="w-16 h-16 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center mx-auto mb-4"
                    animate={
                      card.animation === "pulse" ? { scale: [1, 1.1, 1] } :
                        card.animation === "shake" ? { x: [-2, 2, -2, 2, 0] } :
                          card.animation === "bounce" ? { y: [0, -10, 0] } :
                            card.animation === "rotate" ? { rotate: [0, 10, -10, 0] } : {}
                    }
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <card.icon className="w-8 h-8 text-white" />
                  </motion.div>
                  <h3 className="text-lg font-semibold mb-3 text-cream-50">{card.title}</h3>
                  <p className="text-base text-cream-200">{card.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}

// Features Section Component
function FeaturesSection() {
  const features = [
    {
      icon: Zap,
      title: "AI Job Extraction",
      description: "Paste any LinkedIn job URL and get instant extraction with AI-powered analysis.",
      benefits: ["Smart URL parsing", "Automatic data extraction", "Real-time processing"],
      gradient: "from-accent-500 to-gold-500"
    },
    {
      icon: TrendingUp,
      title: "Smart Job Scoring",
      description: "AI analyzes job requirements against your profile for perfect matches.",
      benefits: ["Resume compatibility", "Skill gap analysis", "Match percentage"],
      gradient: "from-gold-500 to-accent-400"
    },
    {
      icon: Mail,
      title: "Email Integration",
      description: "Connect Gmail to automatically track application responses and interviews.",
      benefits: ["Gmail sync", "Response tracking", "Interview alerts"],
      gradient: "from-accent-400 to-gold-600"
    },
    {
      icon: BarChart3,
      title: "Application Analytics",
      description: "Track your job search progress with detailed insights and metrics.",
      benefits: ["Progress tracking", "Success metrics", "Trend analysis"],
      gradient: "from-gold-600 to-accent-500"
    },
    {
      icon: FileText,
      title: "Resume Optimization",
      description: "Get recruiter-validated feedback to improve your resume's ATS performance.",
      benefits: ["ATS optimization", "Expert feedback", "Score tracking"],
      gradient: "from-accent-500 to-gold-400"
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Enterprise-grade security with local data processing and encryption.",
      benefits: ["End-to-end encryption", "GDPR compliant", "Local processing"],
      gradient: "from-gold-400 to-accent-600"
    }
  ]

  return (
    <section id="features" className="py-20 bg-primary-900">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          className="text-center mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeInVariants}
        >
          <h2 className="text-4xl lg:text-5xl font-neuton text-cream-50 mb-6">
            Everything You Need to Land Your Dream Job
          </h2>
          <p className="text-2xl text-accent-400 max-w-3xl mx-auto">
            From intelligent job extraction to automated tracking - we've built the complete toolkit for modern job seekers.
          </p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 2xl:grid-cols-3 gap-8"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              variants={staggerItem}
              whileHover={{ y: -10, scale: 1.02 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <Card className="premium-card h-full group hover:shadow-card-elevated transition-all duration-500">
                <CardContent className="p-8">
                  <motion.div
                    className={`w-16 h-16 bg-gradient-to-r ${feature.gradient} rounded-2xl flex items-center justify-center mb-6 glow-orange group-hover:glow-gold transition-all duration-300`}
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.6 }}
                  >
                    <feature.icon className="w-8 h-8 text-white" />
                  </motion.div>

                  <h3 className="text-xl font-neuton text-cream-50 mb-4">{feature.title}</h3>
                  <p className="text-lg text-cream-200 mb-6 leading-relaxed">{feature.description}</p>

                  <ul className="space-y-2">
                    {feature.benefits.map((benefit, idx) => (
                      <motion.li
                        key={idx}
                        className="flex items-center text-base text-cream-300"
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                      >
                        <CheckCircle className="w-4 h-4 text-accent-400 mr-2 flex-shrink-0" />
                        {benefit}
                      </motion.li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}

// Solutions Section Component
function SolutionsSection() {
  return (
    <section className="py-20 bg-primary-950 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute top-40 left-1/4 w-96 h-96 bg-gradient-radial from-accent-500/10 to-transparent rounded-full blur-3xl"
          animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
          transition={{ duration: 8, repeat: Infinity }}
        />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        <motion.div
          className="text-center mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeInVariants}
        >
          <h2 className="text-4xl lg:text-5xl font-neuton text-cream-50 mb-6">
            Turn Job Search Chaos Into Organized Success
          </h2>
          <p className="text-2xl text-accent-400 max-w-3xl mx-auto">
            See how JobFlow Pro transforms your job hunting experience from scattered mess to systematic success.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Before/After Comparison */}
          <motion.div
            className="space-y-8"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={staggerContainer}
          >
            <motion.div variants={staggerItem}>
              <h3 className="text-2xl font-neuton text-red-400 mb-4">❌ Without JobFlow Pro</h3>
              <ul className="space-y-3">
                {[
                  "Hours wasted copying job details manually",
                  "Lost applications in email chaos",
                  "No idea which jobs match your skills",
                  "Generic resume feedback from AI tools",
                  "Missing interview invitations"
                ].map((item, index) => (
                  <motion.li
                    key={index}
                    className="flex items-start text-lg text-cream-200"
                    variants={staggerItem}
                  >
                    <X className="w-5 h-5 text-red-400 mr-3 mt-0.5 flex-shrink-0" />
                    {item}
                  </motion.li>
                ))}
              </ul>
            </motion.div>

            <motion.div variants={staggerItem}>
              <h3 className="text-2xl font-neuton text-green-400 mb-4">✅ With JobFlow Pro</h3>
              <ul className="space-y-3">
                {[
                  "One-click job extraction from any URL",
                  "Centralized application tracking dashboard",
                  "AI-powered job-profile matching scores",
                  "Recruiter-validated resume feedback",
                  "Automated email monitoring for responses"
                ].map((item, index) => (
                  <motion.li
                    key={index}
                    className="flex items-start text-lg text-cream-200"
                    variants={staggerItem}
                  >
                    <CheckCircle className="w-5 h-5 text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                    {item}
                  </motion.li>
                ))}
              </ul>
            </motion.div>
          </motion.div>

          {/* Visual Demo */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 100 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <motion.div
              className="bg-gradient-card p-8 rounded-2xl border border-accent-500/20 glow-orange"
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              <div className="space-y-6">
                <div className="flex items-center justify-between mb-6">
                  <h4 className="text-lg font-neuton text-cream-50">Job Extraction Demo</h4>
                  <Badge className="bg-green-500 text-white">Live</Badge>
                </div>

                <div className="space-y-4">
                  <div className="bg-primary-800 p-4 rounded-lg">
                    <div className="text-base text-cream-300 mb-2">LinkedIn URL Input</div>
                    <div className="bg-primary-700 p-2 rounded text-sm text-accent-400 font-mono">
                      linkedin.com/jobs/view/12345...
                    </div>
                  </div>

                  <motion.div
                    className="flex items-center justify-center py-4"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  >
                    <RefreshCw className="w-6 h-6 text-accent-400" />
                  </motion.div>

                  <div className="bg-primary-800 p-4 rounded-lg">
                    <div className="text-base text-cream-300 mb-2">Extracted Data</div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-cream-400">Match Score:</span>
                        <span className="text-green-400 font-bold">92%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-cream-400">Company:</span>
                        <span className="text-cream-200">Google</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-cream-400">Location:</span>
                        <span className="text-cream-200">San Francisco</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

// Social Proof Section Component
function SocialProofSection() {
  const testimonials = [
    {
      name: "Sarah Chen",
      role: "CS Graduate, Stanford",
      company: "Google",
      image: "/api/placeholder/64/64",
      quote: "JobFlow Pro helped me land my dream job at Google. The AI matching saved me weeks of applying to wrong positions.",
      rating: 5
    },
    {
      name: "Marcus Johnson",
      role: "Recent Graduate, MIT",
      company: "Microsoft",
      image: "/api/placeholder/64/64",
      quote: "The resume feedback was game-changing. My ATS score went from 67% to 94% and I started getting more interviews.",
      rating: 5
    },
    {
      name: "Emily Rodriguez",
      role: "MBA Graduate, Wharton",
      company: "McKinsey",
      image: "/api/placeholder/64/64",
      quote: "Finally, a tool that understands what students need. The email integration caught 3 interview invites I would have missed.",
      rating: 5
    }
  ]

  const companies = [
    { name: "Google", logo: "/api/placeholder/120/40" },
    { name: "Microsoft", logo: "/api/placeholder/120/40" },
    { name: "Amazon", logo: "/api/placeholder/120/40" },
    { name: "Apple", logo: "/api/placeholder/120/40" },
    { name: "Meta", logo: "/api/placeholder/120/40" },
    { name: "Netflix", logo: "/api/placeholder/120/40" }
  ]

  return (
    <section className="py-20 bg-primary-900">
      <div className="max-w-7xl mx-auto px-6">
        {/* Stats */}
        <motion.div
          className="text-center mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeInVariants}
        >
          <h2 className="text-4xl lg:text-5xl font-neuton text-cream-50 mb-8">
            Trusted by 10,000+ Students Worldwide
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
            {[
              { value: "10,000+", label: "Active Students" },
              { value: "150+", label: "Universities" },
              { value: "89%", label: "Success Rate" },
              { value: "15+", label: "Hours Saved Weekly" }
            ].map((stat, index) => (
              <motion.div
                key={index}
                className="text-center"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="text-3xl lg:text-4xl font-neuton text-accent-400 mb-2">
                  <CountUpStat value={parseInt(stat.value)} suffix={stat.value.includes('%') ? '%' : '+'} />
                </div>
                <div className="text-lg text-cream-300">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Testimonials */}
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-3 2xl:grid-cols-3 gap-8 mb-16"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={index}
              variants={staggerItem}
              whileHover={{ y: -5 }}
              className="group"
            >
              <Card className="premium-card h-full">
                <CardContent className="p-6">
                  <div className="flex items-center mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 text-gold-400 fill-current" />
                    ))}
                  </div>

                  <blockquote className="text-lg text-cream-200 mb-6 leading-relaxed">
                    "{testimonial.quote}"
                  </blockquote>

                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-primary-700 rounded-full flex items-center justify-center mr-4">
                      <User className="w-6 h-6 text-cream-300" />
                    </div>
                    <div>
                      <div className="font-semibold text-cream-50">{testimonial.name}</div>
                      <div className="text-base text-cream-300">{testimonial.role}</div>
                      <div className="text-base text-accent-400 font-medium">Now at {testimonial.company}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Company Logos */}
        <motion.div
          className="text-center"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeInVariants}
        >
          <p className="text-lg text-cream-300 mb-8">Our students have landed jobs at:</p>
          <div className="flex flex-wrap justify-center items-center gap-8 opacity-60">
            {companies.map((company, index) => (
              <motion.div
                key={index}
                className="text-cream-400 font-semibold text-lg"
                whileHover={{ scale: 1.1, opacity: 1 }}
              >
                {company.name}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

// Pricing Section Component
function PricingSection() {
  const plans = [
    {
      name: "Student Free",
      price: "0",
      period: "Forever",
      description: "Perfect for students just starting their job search",
      features: [
        "5 job extractions per month",
        "Basic resume analysis",
        "Email integration",
        "Application tracking",
        "Community support"
      ],
      highlighted: false,
      cta: "Start Free"
    },
    {
      name: "Job Seeker Pro",
      price: "19",
      period: "month",
      description: "For serious job seekers who want the best results",
      features: [
        "Unlimited job extractions",
        "Advanced AI resume optimization",
        "Priority email monitoring",
        "Advanced analytics",
        "1-on-1 career coaching",
        "Interview preparation",
        "LinkedIn profile optimization"
      ],
      highlighted: true,
      cta: "Start 14-Day Trial"
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "Contact us",
      description: "For universities and career centers",
      features: [
        "Everything in Pro",
        "Bulk student management",
        "Custom integrations",
        "Analytics dashboard",
        "White-label options",
        "Dedicated support"
      ],
      highlighted: false,
      cta: "Contact Sales"
    }
  ]

  return (
    <section id="pricing" className="py-20 bg-primary-950">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          className="text-center mb-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeInVariants}
        >
          <h2 className="text-4xl lg:text-5xl font-neuton text-cream-50 mb-6">
            Simple Pricing That Scales With You
          </h2>
          <p className="text-2xl text-accent-400 max-w-3xl mx-auto">
            Start free as a student, upgrade when you land your job. No hidden fees, cancel anytime.
          </p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-3 2xl:grid-cols-3 gap-8 max-w-6xl mx-auto"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              variants={staggerItem}
              whileHover={{ y: -10, scale: 1.02 }}
              className="relative"
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-gradient-warm text-white px-4 py-1">
                    Most Popular
                  </Badge>
                </div>
              )}

              <Card className={cn(
                "h-full",
                plan.highlighted
                  ? "premium-card-elevated border-accent-500 glow-orange"
                  : "premium-card"
              )}>
                <CardContent className="p-8">
                  <div className="text-center mb-8">
                    <h3 className="text-xl font-neuton text-cream-50 mb-2">{plan.name}</h3>
                    <div className="mb-4">
                      <span className="text-4xl font-neuton text-accent-400">${plan.price}</span>
                      {plan.price !== "Custom" && (
                        <span className="text-cream-300">/{plan.period}</span>
                      )}
                    </div>
                    <p className="text-lg text-cream-200">{plan.description}</p>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start text-base text-cream-200">
                        <CheckCircle className="w-4 h-4 text-accent-400 mr-3 mt-0.5 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <Button
                    className={cn(
                      "w-full",
                      plan.highlighted
                        ? "bg-gradient-warm hover:bg-gradient-gold text-white glow-orange hover:glow-gold"
                        : "bg-primary-700 hover:bg-primary-600 text-cream-50"
                    )}
                  >
                    {plan.cta}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* FAQ */}
        <motion.div
          className="mt-20 max-w-3xl mx-auto"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeInVariants}
        >
          <h3 className="text-2xl font-neuton text-cream-50 text-center mb-8">
            Frequently Asked Questions
          </h3>
          <div className="space-y-4">
            {[
              {
                question: "Is the student plan really free forever?",
                answer: "Yes! We believe every student deserves access to great job search tools. The free plan includes core features with reasonable limits."
              },
              {
                question: "Can I upgrade or downgrade anytime?",
                answer: "Absolutely. Change your plan anytime in your account settings. Upgrades take effect immediately, downgrades at the next billing cycle."
              },
              {
                question: "Do you offer refunds?",
                answer: "Yes, we offer a 30-day money-back guarantee. If you're not satisfied, we'll refund your payment, no questions asked."
              }
            ].map((faq, index) => (
              <Card key={index} className="premium-card">
                <CardContent className="p-6">
                  <h4 className="font-semibold text-cream-50 mb-2">{faq.question}</h4>
                  <p className="text-lg text-cream-200">{faq.answer}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

// CTA Section Component
function CTASection() {
  const { user, signIn } = useAuth()
  const router = useRouter()

  const handleAuthAction = async () => {
    if (user) {
      router.push('/dashboard')
    } else {
      try {
        await signIn()
      } catch (error) {
        console.error('Sign in error:', error)
      }
    }
  }

  return (
    <section className="py-20 bg-primary-900 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <motion.div
          className="absolute top-20 right-1/4 w-96 h-96 bg-gradient-radial from-gold-500/20 to-transparent rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{ duration: 6, repeat: Infinity }}
        />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeInVariants}
        >
          <h2 className="text-4xl lg:text-5xl font-neuton text-cream-50 mb-6">
            Ready to Transform Your Job Search?
          </h2>
          <p className="text-2xl text-accent-400 mb-8 max-w-2xl mx-auto">
            Join thousands of students who've already streamlined their job search with JobFlow Pro.
            Start free today and land your dream job faster.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button
              size="lg"
              className="bg-gradient-warm hover:bg-gradient-gold text-white text-lg px-8 py-4 glow-orange hover:glow-gold transition-all duration-300 hover:scale-105"
              onClick={handleAuthAction}
            >
              {user ? 'Go to Dashboard' : 'Start Free Trial'}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="border-accent-500 text-accent-400 hover:bg-accent-500/10 text-lg px-8 py-4"
            >
              <Calendar className="mr-2 h-5 w-5" />
              Book Demo
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <div className="text-cream-50 font-semibold">Free for Students</div>
              <div className="text-base text-cream-300">No credit card required</div>
            </div>
            <div>
              <Shield className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <div className="text-cream-50 font-semibold">Secure & Private</div>
              <div className="text-base text-cream-300">Your data stays safe</div>
            </div>
            <div>
              <Zap className="w-8 h-8 text-accent-400 mx-auto mb-2" />
              <div className="text-cream-50 font-semibold">Instant Setup</div>
              <div className="text-base text-cream-300">Ready in 2 minutes</div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

// Footer Component
function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-primary-900 border-t border-primary-600 py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Logo size={32} showText={false} />
              <span className="text-xl font-neuton text-gradient-warm">JOBFLOW PRO</span>
            </div>
            <p className="text-cream-300 text-base">
              AI-powered job search automation for students and recent graduates.
            </p>
            <div className="flex space-x-4">
              <Globe className="w-5 h-5 text-cream-400 hover:text-accent-400 cursor-pointer" />
              <Smartphone className="w-5 h-5 text-cream-400 hover:text-accent-400 cursor-pointer" />
            </div>
          </div>

          {/* Product */}
          <div>
            <h3 className="font-semibold text-cream-50 mb-4">Product</h3>
            <ul className="space-y-2 text-base text-cream-300">
              <li><Link href="#features" className="hover:text-accent-400">Features</Link></li>
              <li><Link href="#pricing" className="hover:text-accent-400">Pricing</Link></li>
              <li><Link href="/dashboard" className="hover:text-accent-400">Dashboard</Link></li>
              <li><Link href="/analytics" className="hover:text-accent-400">Analytics</Link></li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="font-semibold text-cream-50 mb-4">Support</h3>
            <ul className="space-y-2 text-base text-cream-300">
              <li><Link href="/help" className="hover:text-accent-400">Help Center</Link></li>
              <li><Link href="/contact" className="hover:text-accent-400">Contact</Link></li>
              <li><Link href="/api-docs" className="hover:text-accent-400">API Docs</Link></li>
              <li><Link href="/status" className="hover:text-accent-400">Status</Link></li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-semibold text-cream-50 mb-4">Legal</h3>
            <ul className="space-y-2 text-base text-cream-300">
              <li><Link href="/privacy" className="hover:text-accent-400">Privacy</Link></li>
              <li><Link href="/terms" className="hover:text-accent-400">Terms</Link></li>
              <li><Link href="/security" className="hover:text-accent-400">Security</Link></li>
              <li><Link href="/cookies" className="hover:text-accent-400">Cookies</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-primary-600 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-cream-400 text-base">
            © {currentYear} JobFlow Pro. All rights reserved.
          </p>
          <p className="text-cream-400 text-base">
            Made with ❤️ for students worldwide
          </p>
        </div>
      </div>
    </footer>
  )
}

// Main Landing Page Component
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-primary-950">
      <Navigation />
      <HeroSection />
      <ProblemSection />
      <FeaturesSection />
      <SolutionsSection />
      <SocialProofSection />
      <PricingSection />
      <CTASection />
      <Footer />
    </div>
  )
}