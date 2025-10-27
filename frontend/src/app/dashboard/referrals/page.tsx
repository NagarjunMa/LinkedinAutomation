"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ReferralRequestForm } from "@/components/referral-request-form"
import { ReferralAnalyticsCard } from "@/components/referral-analytics-card"
import { EnhancedReferralTemplateGenerator } from "@/components/enhanced-referral-template-generator"
import { ReferralTemplateManager } from "@/components/referral-template-manager"
import { referralApi, referralTemplatesAPI } from '@/app/lib/api'
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
    Calendar,
    Save,
    FileText
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




export default function ReferralsPage() {
    const [contacts, setContacts] = useState<Contact[]>([])
    const [filteredContacts, setFilteredContacts] = useState<Contact[]>([])
    const [searchQuery, setSearchQuery] = useState("")
    const [templates, setTemplates] = useState<any[]>([])
    const [templateStats, setTemplateStats] = useState<any | null>(null)
    const [loading, setLoading] = useState(false)
    const [showNewReferralForm, setShowNewReferralForm] = useState(false)
    const [selectedTab, setSelectedTab] = useState("overview")

    // New state for sent referrals
    const [sentReferrals, setSentReferrals] = useState<any[]>([])
    const [loadingSentReferrals, setLoadingSentReferrals] = useState(false)
    const [sentReferralsFilters, setSentReferralsFilters] = useState<any>({ page: 1, page_size: 20 })
    const [totalSentCount, setTotalSentCount] = useState(0)
    const [selectedReferral, setSelectedReferral] = useState<any | null>(null)
    const [selectedTemplate, setSelectedTemplate] = useState<any | null>(null)
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

    // Fetch template data
    const fetchTemplateData = async () => {
        try {
            setLoading(true)
            const [templatesData, statsData] = await Promise.all([
                referralTemplatesAPI.getTemplates(50),
                referralTemplatesAPI.getTemplateStats()
            ])
            setTemplates(templatesData)
            setTemplateStats(statsData)
        } catch (error) {
            console.error('Error fetching template data:', error)
            toast({
                title: "Error",
                description: "Failed to load template data.",
                variant: "destructive",
            })
        } finally {
            setLoading(false)
        }
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

    // Search functionality
    useEffect(() => {
        if (!searchQuery.trim()) {
            setFilteredContacts(contacts)
        } else {
            const filtered = contacts.filter(contact =>
                contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                contact.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
                contact.position.toLowerCase().includes(searchQuery.toLowerCase()) ||
                contact.email.toLowerCase().includes(searchQuery.toLowerCase())
            )
            setFilteredContacts(filtered)
        }
    }, [contacts, searchQuery])

    // Load data when component mounts
    useEffect(() => {
        fetchTemplateData()
    }, [])

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
                            Manage your referral network and generate email templates
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
                                <p className="text-sm text-cream-300">Draft Templates</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {templateStats?.draft_count || 0}
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="premium-card">
                        <CardContent className="p-6 flex items-center space-x-4">
                            <div className="p-3 rounded-full bg-green-500/20">
                                <Mail className="h-6 w-6 text-green-400" />
                            </div>
                            <div>
                                <p className="text-sm text-cream-300">Templates Generated</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {templateStats?.total_templates || 0}
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="premium-card">
                        <CardContent className="p-6 flex items-center space-x-4">
                            <div className="p-3 rounded-full bg-purple-500/20">
                                <Save className="h-6 w-6 text-purple-400" />
                            </div>
                            <div>
                                <p className="text-sm text-cream-300">Response Rate</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {templateStats?.response_rate.toFixed(1) || 0}%
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
                            value="generator"
                            className="data-[state=active]:bg-gradient-warm data-[state=active]:text-white"
                        >
                            <Plus className="h-4 w-4 mr-2" />
                            Generate Template
                        </TabsTrigger>
                        <TabsTrigger
                            value="templates"
                            className="data-[state=active]:bg-gradient-warm data-[state=active]:text-white"
                        >
                            <FileText className="h-4 w-4 mr-2" />
                            Templates
                        </TabsTrigger>
                        <TabsTrigger
                            value="contacts"
                            className="data-[state=active]:bg-gradient-warm data-[state=active]:text-white"
                        >
                            <Users className="h-4 w-4 mr-2" />
                            Contacts
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
                                            {templates.slice(0, 3).map((template) => (
                                                <div key={template.id} className="flex items-center justify-between p-4 rounded-lg bg-primary-800/50 border border-primary-600">
                                                    <div className="flex-1">
                                                        <p className="text-cream-50 font-medium">{template.subject_line}</p>
                                                        <p className="text-cream-300 text-sm">To: {template.contact_name} • {template.contact_company}</p>
                                                        <p className="text-cream-400 text-xs">Created {new Date(template.created_at).toLocaleDateString()}</p>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        {template.was_sent ? (
                                                            <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                                                                <Send className="h-3 w-3 mr-1" />
                                                                Sent
                                                            </Badge>
                                                        ) : (
                                                            <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
                                                                <Clock className="h-3 w-3 mr-1" />
                                                                Draft
                                                            </Badge>
                                                        )}
                                                        <Button variant="ghost" size="sm" className="text-cream-300 hover:text-cream-50">
                                                            View
                                                        </Button>
                                                    </div>
                                                </div>
                                            ))}
                                            {templates.length === 0 && (
                                                <div className="text-center py-8">
                                                    <p className="text-cream-400">No templates created yet</p>
                                                    <p className="text-cream-500 text-sm">Generate your first template to get started</p>
                                                </div>
                                            )}
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
                                    <div className="relative">
                                        <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-cream-400" />
                                        <Input
                                            placeholder="Search contacts..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="pl-10 bg-primary-800 border-primary-600 text-cream-50 w-64"
                                        />
                                    </div>
                                    <Button variant="outline" size="sm" className="border-primary-600 text-cream-300">
                                        <Filter className="h-4 w-4 mr-2" />
                                        Filter
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {filteredContacts.length === 0 ? (
                                        <div className="text-center py-12">
                                            <Users className="h-12 w-12 text-cream-400 mx-auto mb-4" />
                                            <h3 className="text-cream-50 text-lg font-medium mb-2">
                                                {searchQuery ? "No contacts found" : "No contacts yet"}
                                            </h3>
                                            <p className="text-cream-400 mb-4">
                                                {searchQuery
                                                    ? `No contacts match "${searchQuery}"`
                                                    : "Start by generating referral templates to build your contact network"
                                                }
                                            </p>
                                            {!searchQuery && (
                                                <Button
                                                    onClick={() => setSelectedTab("generator")}
                                                    className="bg-accent-500 hover:bg-accent-600 text-white"
                                                >
                                                    <Plus className="h-4 w-4 mr-2" />
                                                    Generate First Template
                                                </Button>
                                            )}
                                        </div>
                                    ) : (
                                        filteredContacts.map((contact) => (
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
                                        ))
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>


                    <TabsContent value="generator" className="space-y-6">
                        <EnhancedReferralTemplateGenerator
                            onTemplateGenerated={(template) => {
                                toast({
                                    title: "Template Generated!",
                                    description: "Your referral template has been created successfully.",
                                })
                                fetchTemplateData()
                            }}
                        />
                    </TabsContent>

                    <TabsContent value="templates" className="space-y-6">
                        <ReferralTemplateManager />
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