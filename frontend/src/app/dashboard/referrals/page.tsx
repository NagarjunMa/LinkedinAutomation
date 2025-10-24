"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ReferralRequestForm } from "@/components/referral-request-form"
import { ReferralAnalyticsCard } from "@/components/referral-analytics-card"
import { referralApi, ReferralDetailedInfo, ReferralFilters } from '@/app/lib/api'
import { useToast } from "@/components/ui/use-toast"
import {
    UserPlus,
    Mail,
    Send,
    Users,
    TrendingUp,
    Star,
    Plus,
    Filter,
    Download,
    BarChart3,
    MessageCircle,
    Clock,
    CheckCircle,
    AlertCircle,
    Search,
    Eye,
    Calendar
} from "lucide-react"
import { cn } from "@/lib/utils"

interface Contact {
    id: string
    name: string
    email: string
    company: string
    position: string
    relationship: string
    lastContact: string
}

interface ReferralDraft {
    id: string
    contactName: string
    jobTitle: string
    company: string
    subject: string
    status: 'draft' | 'sent' | 'responded'
    createdAt: string
    version: number
}

// Mock data for demonstration
const mockContacts: Contact[] = [
    {
        id: "1",
        name: "John Smith",
        email: "john.smith@techcorp.com",
        company: "TechCorp Inc.",
        position: "Senior Software Engineer",
        relationship: "colleague",
        lastContact: "2024-01-15"
    },
    {
        id: "2",
        name: "Sarah Johnson",
        email: "sarah.j@startupxyz.com",
        company: "StartupXYZ",
        position: "Engineering Manager",
        relationship: "linkedin_connection",
        lastContact: "2024-01-10"
    }
]

const mockDrafts: ReferralDraft[] = [
    {
        id: "1",
        contactName: "John Smith",
        jobTitle: "Senior Frontend Developer",
        company: "TechCorp Inc.",
        subject: "Referral Request - Frontend Developer Position",
        status: 'draft',
        createdAt: "2024-01-16",
        version: 1
    },
    {
        id: "2",
        contactName: "Sarah Johnson",
        jobTitle: "Full Stack Engineer",
        company: "StartupXYZ",
        subject: "Referral Request - Full Stack Position",
        status: 'sent',
        createdAt: "2024-01-14",
        version: 2
    }
]

export default function ReferralsPage() {
    const [contacts, setContacts] = useState<Contact[]>(mockContacts)
    const [drafts, setDrafts] = useState<ReferralDraft[]>(mockDrafts)
    const [showNewReferralForm, setShowNewReferralForm] = useState(false)
    const [selectedTab, setSelectedTab] = useState("overview")

    // New state for sent referrals
    const [sentReferrals, setSentReferrals] = useState<ReferralDetailedInfo[]>([])
    const [loadingSentReferrals, setLoadingSentReferrals] = useState(false)
    const [sentReferralsFilters, setSentReferralsFilters] = useState<ReferralFilters>({ page: 1, page_size: 20 })
    const [totalSentCount, setTotalSentCount] = useState(0)
    const [selectedReferral, setSelectedReferral] = useState<ReferralDetailedInfo | null>(null)
    const { toast } = useToast()

    const getStatusBadge = (status: string) => {
        const styles = {
            'draft': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
            'sent': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            'responded': 'bg-green-500/20 text-green-400 border-green-500/30'
        }

        const icons = {
            'draft': <Clock className="h-3 w-3 mr-1" />,
            'sent': <Send className="h-3 w-3 mr-1" />,
            'responded': <CheckCircle className="h-3 w-3 mr-1" />
        }

        return (
            <Badge className={cn("text-xs flex items-center", styles[status as keyof typeof styles])}>
                {icons[status as keyof typeof icons]}
                {status.charAt(0).toUpperCase() + status.slice(1)}
            </Badge>
        )
    }

    // Fetch sent referrals
    const fetchSentReferrals = async () => {
        try {
            setLoadingSentReferrals(true)
            const response = await referralApi.getSentReferrals(sentReferralsFilters)
            setSentReferrals(response.referrals)
            setTotalSentCount(response.total_count)
        } catch (error) {
            console.error('Error fetching sent referrals:', error)
            toast({
                title: "Error",
                description: "Failed to load sent referrals.",
                variant: "destructive",
            })
        } finally {
            setLoadingSentReferrals(false)
        }
    }

    // Load sent referrals when filters change or tab is selected
    useEffect(() => {
        if (selectedTab === 'sent') {
            fetchSentReferrals()
        }
    }, [selectedTab, sentReferralsFilters])

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const markResponseReceived = async (sentId: number) => {
        try {
            await referralApi.markResponseReceived(sentId)
            toast({
                title: "Success",
                description: "Response marked as received!",
            })
            fetchSentReferrals() // Refresh the list
        } catch (error) {
            console.error('Error marking response:', error)
            toast({
                title: "Error",
                description: "Failed to mark response.",
                variant: "destructive",
            })
        }
    }

    const getRelationshipBadge = (relationship: string) => {
        const styles = {
            'colleague': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
            'alumni': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
            'linkedin_connection': 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
            'friend': 'bg-green-500/20 text-green-400 border-green-500/30',
            'other': 'bg-gray-500/20 text-gray-400 border-gray-500/30'
        }

        const displayText = relationship.replace('_', ' ').split(' ').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ')

        return (
            <Badge className={cn("text-xs", styles[relationship as keyof typeof styles])}>
                {displayText}
            </Badge>
        )
    }

    return (
        <div className="min-h-screen bg-primary-950 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold text-cream-50 flex items-center gap-3">
                            <UserPlus className="h-8 w-8 text-accent-400" />
                            Referral Manager
                        </h1>
                        <p className="text-cream-300">
                            Manage your referral network and track email outreach
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            className="border-accent-500/50 text-accent-400 hover:bg-accent-500/20"
                        >
                            <Download className="h-4 w-4 mr-2" />
                            Export Data
                        </Button>
                        <Button
                            onClick={() => setShowNewReferralForm(true)}
                            className="bg-gradient-warm hover:bg-gradient-gold text-white"
                        >
                            <Plus className="h-4 w-4 mr-2" />
                            New Referral Request
                        </Button>
                    </div>
                </div>

                {/* Overview Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card className="premium-card">
                        <CardContent className="p-6 flex items-center space-x-4">
                            <div className="p-3 rounded-full bg-blue-500/20">
                                <Users className="h-6 w-6 text-blue-400" />
                            </div>
                            <div>
                                <p className="text-sm text-cream-300">Total Contacts</p>
                                <p className="text-2xl font-bold text-cream-50">{contacts.length}</p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="premium-card">
                        <CardContent className="p-6 flex items-center space-x-4">
                            <div className="p-3 rounded-full bg-yellow-500/20">
                                <Mail className="h-6 w-6 text-yellow-400" />
                            </div>
                            <div>
                                <p className="text-sm text-cream-300">Draft Emails</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {drafts.filter(d => d.status === 'draft').length}
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="premium-card">
                        <CardContent className="p-6 flex items-center space-x-4">
                            <div className="p-3 rounded-full bg-green-500/20">
                                <Send className="h-6 w-6 text-green-400" />
                            </div>
                            <div>
                                <p className="text-sm text-cream-300">Emails Sent</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {drafts.filter(d => d.status === 'sent').length}
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="premium-card">
                        <CardContent className="p-6 flex items-center space-x-4">
                            <div className="p-3 rounded-full bg-purple-500/20">
                                <MessageCircle className="h-6 w-6 text-purple-400" />
                            </div>
                            <div>
                                <p className="text-sm text-cream-300">Responses</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {drafts.filter(d => d.status === 'responded').length}
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Main Content Tabs */}
                <Tabs value={selectedTab} onValueChange={setSelectedTab}>
                    <TabsList className="grid w-full grid-cols-5 bg-primary-800 border border-primary-600">
                        <TabsTrigger
                            value="overview"
                            className="data-[state=active]:bg-gradient-warm data-[state=active]:text-white"
                        >
                            <BarChart3 className="h-4 w-4 mr-2" />
                            Overview
                        </TabsTrigger>
                        <TabsTrigger
                            value="contacts"
                            className="data-[state=active]:bg-gradient-warm data-[state=active]:text-white"
                        >
                            <Users className="h-4 w-4 mr-2" />
                            Contacts
                        </TabsTrigger>
                        <TabsTrigger
                            value="drafts"
                            className="data-[state=active]:bg-gradient-warm data-[state=active]:text-white"
                        >
                            <Mail className="h-4 w-4 mr-2" />
                            Email Drafts
                        </TabsTrigger>
                        <TabsTrigger
                            value="sent"
                            className="data-[state=active]:bg-gradient-warm data-[state=active]:text-white"
                        >
                            <Send className="h-4 w-4 mr-2" />
                            Sent Referrals
                        </TabsTrigger>
                        <TabsTrigger
                            value="analytics"
                            className="data-[state=active]:bg-gradient-warm data-[state=active]:text-white"
                        >
                            <TrendingUp className="h-4 w-4 mr-2" />
                            Analytics
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-6">
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <div className="lg:col-span-2 space-y-6">
                                {/* Recent Activity */}
                                <Card className="premium-card">
                                    <CardHeader>
                                        <CardTitle className="text-cream-50 flex items-center gap-2">
                                            <Clock className="h-5 w-5 text-accent-400" />
                                            Recent Activity
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-4">
                                            {drafts.slice(0, 3).map((draft) => (
                                                <div key={draft.id} className="flex items-center justify-between p-4 rounded-lg bg-primary-800/50 border border-primary-600">
                                                    <div className="flex-1">
                                                        <p className="text-cream-50 font-medium">{draft.subject}</p>
                                                        <p className="text-cream-300 text-sm">To: {draft.contactName} • {draft.company}</p>
                                                        <p className="text-cream-400 text-xs">Created {draft.createdAt}</p>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        {getStatusBadge(draft.status)}
                                                        <Button variant="ghost" size="sm" className="text-cream-300 hover:text-cream-50">
                                                            View
                                                        </Button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Analytics Card */}
                            <div>
                                <ReferralAnalyticsCard
                                    title="📊 Email Analytics"
                                    showActions={false}
                                />
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="contacts" className="space-y-6">
                        <Card className="premium-card">
                            <CardHeader className="flex flex-row items-center justify-between">
                                <CardTitle className="text-cream-50">My Contacts</CardTitle>
                                <div className="flex gap-2">
                                    <Button variant="outline" size="sm" className="border-primary-600 text-cream-300">
                                        <Filter className="h-4 w-4 mr-2" />
                                        Filter
                                    </Button>
                                    <Button variant="outline" size="sm" className="border-primary-600 text-cream-300">
                                        <Search className="h-4 w-4 mr-2" />
                                        Search
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {contacts.map((contact) => (
                                        <div key={contact.id} className="flex items-center justify-between p-4 rounded-lg bg-primary-800/50 border border-primary-600 hover:bg-primary-800 transition-colors">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="text-cream-50 font-medium">{contact.name}</h3>
                                                    {getRelationshipBadge(contact.relationship)}
                                                </div>
                                                <p className="text-cream-300 text-sm">{contact.position} at {contact.company}</p>
                                                <p className="text-cream-400 text-xs">{contact.email} • Last contact: {contact.lastContact}</p>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Button variant="outline" size="sm" className="border-accent-500/50 text-accent-400 hover:bg-accent-500/20">
                                                    <Mail className="h-4 w-4 mr-2" />
                                                    Request Referral
                                                </Button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="drafts" className="space-y-6">
                        <Card className="premium-card">
                            <CardHeader className="flex flex-row items-center justify-between">
                                <CardTitle className="text-cream-50">Email Drafts</CardTitle>
                                <div className="flex gap-2">
                                    <Button variant="outline" size="sm" className="border-primary-600 text-cream-300">
                                        <Filter className="h-4 w-4 mr-2" />
                                        Filter
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {drafts.map((draft) => (
                                        <div key={draft.id} className="flex items-center justify-between p-4 rounded-lg bg-primary-800/50 border border-primary-600 hover:bg-primary-800 transition-colors">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3 mb-2">
                                                    <h3 className="text-cream-50 font-medium">{draft.subject}</h3>
                                                    {getStatusBadge(draft.status)}
                                                </div>
                                                <p className="text-cream-300 text-sm">To: {draft.contactName} • {draft.company}</p>
                                                <p className="text-cream-400 text-xs">
                                                    Version {draft.version} • Created {draft.createdAt}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Button variant="outline" size="sm" className="border-primary-600 text-cream-300">
                                                    Edit
                                                </Button>
                                                {draft.status === 'draft' && (
                                                    <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white">
                                                        <Send className="h-4 w-4 mr-2" />
                                                        Send
                                                    </Button>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="analytics" className="space-y-6">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <ReferralAnalyticsCard
                                title="📈 Performance Overview"
                                showActions={true}
                            />
                            <ReferralAnalyticsCard
                                title="📊 Response Analytics"
                                showActions={false}
                            />
                        </div>
                    </TabsContent>

                    {/* Sent Referrals Tab */}
                    <TabsContent value="sent" className="space-y-6">
                        {loadingSentReferrals ? (
                            <div className="space-y-4">
                                {[...Array(3)].map((_, i) => (
                                    <Card key={i} className="premium-card">
                                        <CardContent className="p-6">
                                            <div className="animate-pulse space-y-3">
                                                <div className="h-4 bg-primary-700 rounded w-1/3"></div>
                                                <div className="h-3 bg-primary-700 rounded w-1/2"></div>
                                                <div className="h-3 bg-primary-700 rounded w-2/3"></div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        ) : sentReferrals.length === 0 ? (
                            <Card className="premium-card">
                                <CardContent className="p-12 text-center">
                                    <Send className="w-16 h-16 text-cream-600 mx-auto mb-4" />
                                    <h3 className="text-lg font-semibold text-cream-50 mb-2">No Sent Referrals</h3>
                                    <p className="text-cream-400 mb-4">
                                        You haven't sent any referral requests yet. Create and send your first referral to get started!
                                    </p>
                                    <Button
                                        onClick={() => setShowNewReferralForm(true)}
                                        className="bg-gradient-warm hover:bg-gradient-warm/90"
                                    >
                                        <Plus className="w-4 h-4 mr-2" />
                                        Create New Referral
                                    </Button>
                                </CardContent>
                            </Card>
                        ) : (
                            <div className="space-y-4">
                                {/* Filters */}
                                <Card className="premium-card">
                                    <CardContent className="p-4">
                                        <div className="flex items-center gap-4">
                                            <div className="flex-1">
                                                <input
                                                    type="text"
                                                    placeholder="Filter by company..."
                                                    value={sentReferralsFilters.company_filter || ''}
                                                    onChange={(e) => setSentReferralsFilters(prev => ({
                                                        ...prev,
                                                        company_filter: e.target.value,
                                                        page: 1
                                                    }))}
                                                    className="w-full px-3 py-2 bg-primary-800 border border-primary-600 rounded text-cream-50 placeholder-cream-400"
                                                />
                                            </div>
                                            <Badge variant="secondary" className="bg-accent-500/20 text-accent-400">
                                                {totalSentCount} Total
                                            </Badge>
                                        </div>
                                    </CardContent>
                                </Card>

                                {/* Referrals List */}
                                {sentReferrals.map((referral) => (
                                    <Card key={referral.sent_id} className="premium-card hover:border-accent-500/50 transition-colors">
                                        <CardContent className="p-6">
                                            <div className="flex items-start justify-between mb-4">
                                                <div className="flex items-start space-x-4">
                                                    <div className="p-2 bg-accent-500/20 rounded-lg">
                                                        <Users className="w-6 h-6 text-accent-400" />
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <h3 className="text-lg font-semibold text-cream-50">{referral.contact_name}</h3>
                                                            {referral.response_received ? (
                                                                <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
                                                                    <CheckCircle className="w-3 h-3 mr-1" />
                                                                    Response Received
                                                                </Badge>
                                                            ) : (
                                                                <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/50">
                                                                    <Clock className="w-3 h-3 mr-1" />
                                                                    Pending Response
                                                                </Badge>
                                                            )}
                                                        </div>
                                                        <div className="flex items-center gap-4 text-sm text-cream-300 mb-2">
                                                            <div className="flex items-center gap-1">
                                                                <Mail className="w-4 h-4" />
                                                                {referral.contact_email}
                                                            </div>
                                                            <div className="flex items-center gap-1">
                                                                <Users className="w-4 h-4" />
                                                                {referral.company}
                                                            </div>
                                                            {referral.position && (
                                                                <div className="flex items-center gap-1">
                                                                    <Badge variant="outline" className="text-xs">
                                                                        {referral.position}
                                                                    </Badge>
                                                                </div>
                                                            )}
                                                        </div>
                                                        <div className="flex items-center gap-1 text-xs text-cream-400">
                                                            <Calendar className="w-3 h-3" />
                                                            Sent {formatDate(referral.sent_at)}
                                                            {referral.response_received && referral.response_date && (
                                                                <>
                                                                    <span className="mx-2">•</span>
                                                                    <CheckCircle className="w-3 h-3" />
                                                                    Response {formatDate(referral.response_date)}
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {!referral.response_received && (
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() => markResponseReceived(referral.sent_id)}
                                                            className="border-green-500/50 text-green-400 hover:bg-green-500/10"
                                                        >
                                                            <CheckCircle className="w-4 h-4 mr-1" />
                                                            Mark Response
                                                        </Button>
                                                    )}
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => setSelectedReferral(referral)}
                                                        className="text-accent-400 hover:text-accent-300 hover:bg-accent-500/10"
                                                    >
                                                        <Eye className="w-4 h-4 mr-1" />
                                                        View Details
                                                    </Button>
                                                </div>
                                            </div>

                                            {/* Job Information */}
                                            {(referral.job_title || referral.job_company) && (
                                                <div className="border-t border-primary-700/50 pt-4">
                                                    <div className="flex items-center gap-2 text-sm">
                                                        <Users className="w-4 h-4 text-accent-400" />
                                                        <span className="text-cream-300">
                                                            Applied for: <span className="text-cream-50">{referral.job_title}</span>
                                                            {referral.job_company && referral.job_company !== referral.company && (
                                                                <span> at {referral.job_company}</span>
                                                            )}
                                                        </span>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Email Preview */}
                                            {referral.email_subject && (
                                                <div className="border-t border-primary-700/50 pt-4 mt-4">
                                                    <div className="flex items-start gap-2">
                                                        <MessageCircle className="w-4 h-4 text-accent-400 mt-1" />
                                                        <div className="flex-1">
                                                            <p className="text-sm text-cream-300 mb-1">
                                                                Subject: <span className="text-cream-50">{referral.email_subject}</span>
                                                            </p>
                                                            {referral.email_body && (
                                                                <p className="text-xs text-cream-400 line-clamp-2">
                                                                    {referral.email_body.slice(0, 150)}...
                                                                </p>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>
                                ))}

                                {/* Pagination */}
                                {Math.ceil(totalSentCount / (sentReferralsFilters.page_size || 20)) > 1 && (
                                    <div className="flex items-center justify-center space-x-2">
                                        <Button
                                            variant="outline"
                                            disabled={(sentReferralsFilters.page || 1) === 1}
                                            onClick={() => setSentReferralsFilters(prev => ({
                                                ...prev,
                                                page: (prev.page || 1) - 1
                                            }))}
                                            className="border-primary-600 text-cream-300"
                                        >
                                            Previous
                                        </Button>
                                        <span className="text-cream-300 px-4">
                                            Page {sentReferralsFilters.page || 1} of {Math.ceil(totalSentCount / (sentReferralsFilters.page_size || 20))}
                                        </span>
                                        <Button
                                            variant="outline"
                                            disabled={(sentReferralsFilters.page || 1) >= Math.ceil(totalSentCount / (sentReferralsFilters.page_size || 20))}
                                            onClick={() => setSentReferralsFilters(prev => ({
                                                ...prev,
                                                page: (prev.page || 1) + 1
                                            }))}
                                            className="border-primary-600 text-cream-300"
                                        >
                                            Next
                                        </Button>
                                    </div>
                                )}
                            </div>
                        )}
                    </TabsContent>
                </Tabs>

                {/* New Referral Request Form Modal */}
                {showNewReferralForm && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                        <div className="bg-primary-800 rounded-lg border border-primary-600 max-w-4xl w-full max-h-[90vh] overflow-hidden">
                            <div className="p-6 border-b border-primary-600 flex items-center justify-between">
                                <h2 className="text-xl font-semibold text-cream-50">New Referral Request</h2>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setShowNewReferralForm(false)}
                                    className="text-cream-300 hover:text-cream-50"
                                >
                                    ×
                                </Button>
                            </div>
                            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                                <ReferralRequestForm
                                    jobId="sample-job-id"
                                    jobTitle="Sample Job Position"
                                    companyName="Sample Company"
                                    onSuccess={() => {
                                        setShowNewReferralForm(false)
                                        // Refresh data or show success message
                                    }}
                                    className="border-0 shadow-none bg-transparent"
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Detailed Referral View Modal */}
                {selectedReferral && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                        <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden bg-primary-900 border-primary-700">
                            <CardHeader className="pb-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-cream-50">{selectedReferral.contact_name}</CardTitle>
                                        <p className="text-cream-400">
                                            {selectedReferral.company} • {formatDate(selectedReferral.sent_at)}
                                        </p>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        onClick={() => setSelectedReferral(null)}
                                        className="text-cream-400 hover:text-cream-50"
                                    >
                                        ×
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4 overflow-y-auto">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-cream-400 text-sm">Email</p>
                                        <p className="text-cream-50">{selectedReferral.contact_email}</p>
                                    </div>
                                    <div>
                                        <p className="text-cream-400 text-sm">Position</p>
                                        <p className="text-cream-50">{selectedReferral.position || 'Not specified'}</p>
                                    </div>
                                    <div>
                                        <p className="text-cream-400 text-sm">Relationship</p>
                                        <p className="text-cream-50">{selectedReferral.contact_relationship || 'Not specified'}</p>
                                    </div>
                                    <div>
                                        <p className="text-cream-400 text-sm">Template Used</p>
                                        <p className="text-cream-50">{selectedReferral.template_used || 'Custom'}</p>
                                    </div>
                                </div>

                                {selectedReferral.email_subject && (
                                    <div>
                                        <p className="text-cream-400 text-sm mb-2">Email Subject</p>
                                        <p className="text-cream-50 p-3 bg-primary-800/50 rounded border border-primary-600">
                                            {selectedReferral.email_subject}
                                        </p>
                                    </div>
                                )}

                                {selectedReferral.email_body && (
                                    <div>
                                        <p className="text-cream-400 text-sm mb-2">Email Content</p>
                                        <div className="p-4 bg-primary-800/50 rounded border border-primary-600 max-h-64 overflow-y-auto">
                                            <pre className="text-cream-50 text-sm whitespace-pre-wrap font-sans">
                                                {selectedReferral.email_body}
                                            </pre>
                                        </div>
                                    </div>
                                )}

                                <div className="flex justify-end gap-2 pt-4 border-t border-primary-700">
                                    {!selectedReferral.response_received && (
                                        <Button
                                            onClick={() => {
                                                markResponseReceived(selectedReferral.sent_id)
                                                setSelectedReferral(null)
                                            }}
                                            className="bg-green-500/20 border border-green-500/50 text-green-400 hover:bg-green-500/30"
                                        >
                                            <CheckCircle className="w-4 h-4 mr-2" />
                                            Mark Response Received
                                        </Button>
                                    )}
                                    <Button
                                        variant="outline"
                                        onClick={() => setSelectedReferral(null)}
                                        className="border-primary-600 text-cream-300"
                                    >
                                        Close
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>
        </div>
    )
}