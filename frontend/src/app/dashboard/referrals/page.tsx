"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ReferralRequestForm } from "@/components/referral-request-form"
import { EnhancedReferralTemplateGenerator } from "@/components/enhanced-referral-template-generator"
import { ReferralTemplateManager } from "@/components/referral-template-manager"
import { referralApi, referralTemplatesAPI } from '@/app/lib/api/referral'
import { useToast } from "@/components/ui/use-toast"
import {
    UserPlus,
    Mail,
    Send,
    Users,
    Plus,
    Filter,
    Download,
    Clock,
    CheckCircle,
    Search,
    FileText,
    Sparkles,
    ArrowRight,
    TrendingUp,
    X
} from "lucide-react"
import { cn } from "@/lib/utils"
// Import noise pattern if needed, or just use the class if defined globally. 
// Assuming NOISE_PATTERN from design file is not globally available as a class, we'll try to use the same background color.
import { NOISE_PATTERN } from "@/lib/constants/resume-evaluation-design"

interface Contact {
    id: string
    name: string
    email: string
    company: string
    position: string
    relationship: string
    lastContact: string
    status: string // Added status
}

interface ReferralTemplate {
    id: string;
    name: string;
    content: string;
    subject_line?: string;
    contact_name?: string;
    contact_company?: string;
    created_at?: string;
    was_sent?: boolean;
    [key: string]: unknown;
}

interface SentReferral {
    contact_name: string;
    company: string;
    sent_at: string;
    contact_email: string;
    position?: string;
    contact_relationship?: string;
    template_used?: string;
    email_subject?: string;
    email_body?: string;
    response_received?: boolean;
    response_date?: string;
    sent_id: number;
    job_title?: string;
    job_company?: string;
    job_id?: number | string;
    job_location?: string;
    status?: string; // computed or added
    [key: string]: unknown;
}

interface TemplateStats {
    total: number;
    draft_count?: number;
    total_templates?: number;
    response_rate?: number;
    [key: string]: unknown;
}

export default function ReferralsPage() {
    const [contacts] = useState<Contact[]>([])
    const [filteredContacts, setFilteredContacts] = useState<Contact[]>([])
    const [searchQuery, setSearchQuery] = useState("")
    const [templates, setTemplates] = useState<ReferralTemplate[]>([])
    const [templateStats, setTemplateStats] = useState<TemplateStats | null>(null)
    const [_loading, setLoading] = useState(false)
    const [showNewReferralForm, setShowNewReferralForm] = useState(false)
    const [selectedTab, setSelectedTab] = useState<string>("overview")

    // New state for sent referrals
    const [_sentReferralsFilters] = useState<Record<string, unknown>>({ page: 1, page_size: 20 })
    const [selectedReferral, setSelectedReferral] = useState<SentReferral | null>(null)
    const { toast } = useToast()

    const getStatusBadge = (status: string) => {
        const styles = {
            'draft': 'bg-amber-100 text-amber-700 border-amber-200',
            'sent': 'bg-blue-100 text-blue-700 border-blue-200',
            'responded': 'bg-emerald-100 text-emerald-700 border-emerald-200'
        }

        const icons = {
            'draft': <Clock className="h-3 w-3 mr-1" />,
            'sent': <Send className="h-3 w-3 mr-1" />,
            'responded': <CheckCircle className="h-3 w-3 mr-1" />
        }

        return (
            <Badge className={cn("px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border", styles[status as keyof typeof styles])}>
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
                referralTemplatesAPI.getStats()
            ])
            setTemplates(templatesData as unknown as ReferralTemplate[])
            setTemplateStats(statsData as unknown as TemplateStats)
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
            setLoading(true)
            const response = await referralApi.getSentReferrals(_sentReferralsFilters as { page: number; page_size: number })
            const referrals = (response.referrals as SentReferral[]) || []
            if (referrals && referrals.length > 0) {
                setSelectedReferral(referrals[0])
            } else {
                setSelectedReferral(null)
            }
        } catch (error: unknown) {
            console.error('Error fetching sent referrals:', error)
            toast({
                title: "Error",
                description: "Failed to load sent referrals.",
                variant: "destructive",
            })
        } finally {
            setLoading(false)
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
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    // Load sent referrals when filters change or tab is selected
    useEffect(() => {
        if (selectedTab === 'sent') {
            fetchSentReferrals()
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedTab, _sentReferralsFilters])

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
        const displayText = relationship.replace('_', ' ').split(' ').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ')

        return (
            <Badge className="bg-[#3b3b3b]/5 text-[#3b3b3b] border-[#3b3b3b]/10 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                {displayText}
            </Badge>
        )
    }

    return (
        <div className="min-h-screen bg-[#f0eff2] dark:bg-[#0a0a0a] text-[#3b3b3b] dark:text-[#f0eff2] relative transition-colors duration-300">
            {/* Noise Pattern Overlay */}
            {NOISE_PATTERN && (
                <div
                    className="absolute inset-0 pointer-events-none opacity-[0.4] dark:opacity-[0.2] mix-blend-overlay z-0"
                    style={{ backgroundImage: `url("${NOISE_PATTERN}")` }}
                />
            )}

            <div className="relative z-10 p-8">
                <div className="max-w-7xl mx-auto space-y-8">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-2xl bg-[#3b3b3b] dark:bg-white flex items-center justify-center text-white dark:text-black shadow-xl">
                                    <UserPlus className="h-6 w-6" />
                                </div>
                                <h1 className="text-4xl font-black tracking-tighter text-[#3b3b3b] dark:text-white uppercase">
                                    Referral Manager
                                </h1>
                            </div>
                            <p className="text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 font-medium ml-[60px]">
                                Strategic Network & Template Orchestration
                            </p>
                        </div>
                        <div className="flex gap-4">
                            <Button
                                variant="outline"
                                className="bg-white/50 dark:bg-black/50 backdrop-blur-sm border-white dark:border-[#3b3b3b] hover:bg-white dark:hover:bg-[#1c1c1c] text-[#3b3b3b] dark:text-[#f0eff2] font-black text-xs uppercase tracking-widest px-6 py-6 rounded-2xl transition-all shadow-sm"
                            >
                                <Download className="h-4 w-4 mr-2" />
                                Export Data
                            </Button>
                            <Button
                                onClick={() => setShowNewReferralForm(true)}
                                className="bg-[#3b3b3b] dark:bg-white hover:bg-black dark:hover:bg-[#e5e5e5] text-white dark:text-black font-black text-xs uppercase tracking-widest px-8 py-6 rounded-2xl transition-all shadow-xl hover:shadow-2xl hover:scale-[1.02] active:scale-95"
                            >
                                <Plus className="h-4 w-4 mr-2" />
                                New Request
                            </Button>
                        </div>
                    </div>

                    {/* Overview Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div className="bg-white dark:bg-[#1c1c1c] p-8 rounded-[32px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-sm hover:shadow-xl transition-all group">
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 rounded-2xl bg-[#3b3b3b]/5 dark:bg-[#f0eff2]/10 text-[#3b3b3b] dark:text-[#f0eff2] group-hover:scale-110 transition-transform">
                                    <Users className="h-6 w-6" />
                                </div>
                                <span className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Active</span>
                            </div>
                            <div>
                                <p className="text-4xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tighter">{contacts.length}</p>
                                <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 mt-1">Total Contacts</p>
                            </div>
                        </div>

                        <div className="bg-white dark:bg-[#1c1c1c] p-8 rounded-[32px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-sm hover:shadow-xl transition-all group">
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 rounded-2xl bg-amber-500/10 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 group-hover:scale-110 transition-transform">
                                    <FileText className="h-6 w-6" />
                                </div>
                                <span className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Pending</span>
                            </div>
                            <div>
                                <p className="text-4xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tighter">
                                    {typeof templateStats?.draft_count === 'number' ? templateStats.draft_count : 0}
                                </p>
                                <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 mt-1">Draft Templates</p>
                            </div>
                        </div>

                        <div className="bg-white dark:bg-[#1c1c1c] p-8 rounded-[32px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-sm hover:shadow-xl transition-all group">
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 rounded-2xl bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform">
                                    <Sparkles className="h-6 w-6" />
                                </div>
                                <span className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Generated</span>
                            </div>
                            <div>
                                <p className="text-4xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tighter">
                                    {typeof templateStats?.total_templates === 'number' ? templateStats.total_templates : 0}
                                </p>
                                <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 mt-1">Total Templates</p>
                            </div>
                        </div>

                        <div className="bg-white dark:bg-[#1c1c1c] p-8 rounded-[32px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-sm hover:shadow-xl transition-all group">
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 rounded-2xl bg-blue-500/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
                                    <TrendingUp className="h-6 w-6" />
                                </div>
                                <span className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Success</span>
                            </div>
                            <div>
                                <p className="text-4xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tighter">
                                    {typeof templateStats?.response_rate === 'number' ? `${templateStats.response_rate.toFixed(1)}%` : '0%'}
                                </p>
                                <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 mt-1">Response Rate</p>
                            </div>
                        </div>
                    </div>

                    <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
                        <div className="bg-white/50 dark:bg-[#1c1c1c]/50 backdrop-blur-md p-2 rounded-2xl border border-white dark:border-[#3b3b3b] inline-flex shadow-sm">
                            <TabsList className="bg-transparent h-auto p-0 gap-2">
                                <TabsTrigger
                                    value="overview"
                                    className="px-6 py-3 rounded-xl data-[state=active]:bg-[#3b3b3b] dark:data-[state=active]:bg-white data-[state=active]:text-white dark:data-[state=active]:text-black data-[state=active]:shadow-lg font-black text-xs uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 transition-all hover:text-[#3b3b3b] dark:hover:text-[#f0eff2]"
                                >
                                    Overview
                                </TabsTrigger>
                                <TabsTrigger
                                    value="generator"
                                    className="px-6 py-3 rounded-xl data-[state=active]:bg-[#3b3b3b] dark:data-[state=active]:bg-white data-[state=active]:text-white dark:data-[state=active]:text-black data-[state=active]:shadow-lg font-black text-xs uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 transition-all hover:text-[#3b3b3b] dark:hover:text-[#f0eff2]"
                                >
                                    Generate Template
                                </TabsTrigger>
                                <TabsTrigger
                                    value="templates"
                                    className="px-6 py-3 rounded-xl data-[state=active]:bg-[#3b3b3b] dark:data-[state=active]:bg-white data-[state=active]:text-white dark:data-[state=active]:text-black data-[state=active]:shadow-lg font-black text-xs uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 transition-all hover:text-[#3b3b3b] dark:hover:text-[#f0eff2]"
                                >
                                    Templates
                                </TabsTrigger>
                                <TabsTrigger
                                    value="contacts"
                                    className="px-6 py-3 rounded-xl data-[state=active]:bg-[#3b3b3b] dark:data-[state=active]:bg-white data-[state=active]:text-white dark:data-[state=active]:text-black data-[state=active]:shadow-lg font-black text-xs uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 transition-all hover:text-[#3b3b3b] dark:hover:text-[#f0eff2]"
                                >
                                    Contacts
                                </TabsTrigger>
                            </TabsList>
                        </div>

                        <TabsContent value="overview" className="space-y-6">
                            {/* Recent Activity */}
                            <div className="bg-white dark:bg-[#1c1c1c] p-8 rounded-[40px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-xl">
                                <div className="flex items-center justify-between mb-8">
                                    <h3 className="text-2xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tight flex items-center gap-3">
                                        <Clock className="h-6 w-6 text-[#3b3b3b]/40 dark:text-[#f0eff2]/40" />
                                        Recent Activity
                                    </h3>
                                    <Button variant="ghost" className="text-xs font-black uppercase tracking-widest text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 hover:text-[#3b3b3b] dark:hover:text-[#f0eff2] hover:bg-transparent">
                                        View All <ArrowRight className="ml-2 h-3 w-3" />
                                    </Button>
                                </div>

                                <div className="space-y-4">
                                    {templates.slice(0, 3).map((template) => (
                                        <div key={template.id as string} className="bg-[#f0eff2]/30 dark:bg-[#0a0a0a]/30 p-6 rounded-3xl border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 flex items-center justify-between hover:bg-[#f0eff2]/50 dark:hover:bg-[#0a0a0a]/50 transition-colors group cursor-pointer" onClick={() => setSelectedTab("templates")}>
                                            <div className="flex items-center gap-4">
                                                <div className="w-12 h-12 rounded-2xl bg-white dark:bg-black/50 flex items-center justify-center text-[#3b3b3b] dark:text-[#f0eff2] shadow-sm border border-[#3b3b3b]/5 dark:border-[#f0eff2]/5">
                                                    <FileText className="h-5 w-5" />
                                                </div>
                                                <div>
                                                    <h4 className="text-[#3b3b3b] dark:text-[#f0eff2] font-bold text-lg leading-tight group-hover:text-blue-600 transition-colors">
                                                        {template.subject_line as string}
                                                    </h4>
                                                    <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40 mt-1">
                                                        Generated {formatDate(template.created_at as string)}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <Badge className="bg-white dark:bg-black/50 text-[#3b3b3b] dark:text-[#f0eff2] border-[#3b3b3b]/10 dark:border-[#f0eff2]/10 px-3 py-1 rounded-xl text-[10px] font-bold uppercase tracking-wider">
                                                    {template.template_style as string}
                                                </Badge>
                                                <ArrowRight className="h-4 w-4 text-[#3b3b3b]/20 dark:text-[#f0eff2]/20 group-hover:text-[#3b3b3b] dark:group-hover:text-[#f0eff2] transition-colors" />
                                            </div>
                                        </div>
                                    ))}

                                    {templates.length === 0 && (
                                        <div className="text-center py-16 bg-[#f0eff2]/30 dark:bg-[#0a0a0a]/30 rounded-3xl border border-dashed border-[#3b3b3b]/10 dark:border-[#f0eff2]/10">
                                            <div className="w-16 h-16 rounded-full bg-[#3b3b3b]/5 dark:bg-[#f0eff2]/5 flex items-center justify-center mx-auto mb-4">
                                                <Sparkles className="h-8 w-8 text-[#3b3b3b]/40 dark:text-[#f0eff2]/40" />
                                            </div>
                                            <h3 className="text-lg font-black text-[#3b3b3b] dark:text-[#f0eff2] mb-2 uppercase tracking-tight">No templates created yet</h3>
                                            <p className="text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 text-sm max-w-sm mx-auto mb-8">Start by generating your first AI-powered referral template to grow your network.</p>
                                            <Button
                                                onClick={() => setSelectedTab("generator")}
                                                className="bg-[#3b3b3b] dark:bg-white hover:bg-black dark:hover:bg-[#e5e5e5] text-white dark:text-black font-black text-xs uppercase tracking-widest px-8 py-4 rounded-xl shadow-lg hover:shadow-xl transition-all"
                                            >
                                                Create Template
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="generator">
                            <div className="bg-white dark:bg-[#1c1c1c] p-8 rounded-[40px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-xl">
                                <EnhancedReferralTemplateGenerator onTemplateGenerated={() => {
                                    fetchTemplateData() // Refresh stats
                                }} />
                            </div>
                        </TabsContent>

                        <TabsContent value="templates">
                            <ReferralTemplateManager />
                        </TabsContent>

                        <TabsContent value="contacts">
                            <div className="bg-white dark:bg-[#1c1c1c] p-8 rounded-[40px] border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 shadow-xl space-y-6">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-2xl font-black text-[#3b3b3b] dark:text-[#f0eff2] tracking-tight flex items-center gap-3">
                                        <Users className="h-6 w-6 text-[#3b3b3b]/40 dark:text-[#f0eff2]/40" />
                                        Details
                                    </h3>
                                    <div className="flex gap-2">
                                        <div className="relative">
                                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#3b3b3b]/40 dark:text-[#f0eff2]/40" />
                                            <Input
                                                placeholder="SEARCH CONTACTS..."
                                                className="pl-9 bg-[#f0eff2]/50 dark:bg-[#0a0a0a]/50 border-transparent focus:bg-white dark:focus:bg-[#1c1c1c] focus:border-[#3b3b3b]/10 dark:focus:border-[#f0eff2]/10 rounded-xl w-64 text-xs font-bold tracking-wide uppercase placeholder:text-[#3b3b3b]/30 dark:placeholder:text-[#f0eff2]/30 text-[#3b3b3b] dark:text-[#f0eff2]"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                            />
                                        </div>
                                        <Button variant="outline" className="border-[#3b3b3b]/10 text-[#3b3b3b] rounded-xl px-3 hover:bg-[#3b3b3b]/5">
                                            <Filter className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>

                                {filteredContacts.length > 0 ? (
                                    <div className="grid gap-4">
                                        {filteredContacts.map((contact) => (
                                            <div key={contact.id} className="bg-[#f0eff2]/30 p-6 rounded-3xl border border-[#3b3b3b]/5 hover:bg-white hover:shadow-lg transition-all group">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-4">
                                                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#3b3b3b] to-black text-white flex items-center justify-center font-black text-sm uppercase shadow-md">
                                                            {contact.name.substring(0, 2)}
                                                        </div>
                                                        <div>
                                                            <h4 className="text-[#3b3b3b] font-bold text-lg">{contact.name}</h4>
                                                            <div className="flex items-center gap-2 text-xs font-medium text-[#3b3b3b]/60 mt-1">
                                                                <span className="bg-white px-2 py-0.5 rounded border border-[#3b3b3b]/5">{contact.position}</span>
                                                                <span>at</span>
                                                                <span className="font-bold text-[#3b3b3b]">{contact.company}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-4">
                                                        <div className="text-right mr-4">
                                                            <div className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 mb-1">Status</div>
                                                            {getStatusBadge(contact.status)}
                                                        </div>
                                                        <div className="text-right mr-4">
                                                            <div className="text-[10px] font-black uppercase tracking-widest text-[#3b3b3b]/40 mb-1">Relationship</div>
                                                            {getRelationshipBadge(contact.relationship)}
                                                        </div>
                                                        <Button variant="ghost" className="rounded-xl hover:bg-[#3b3b3b]/5 text-[#3b3b3b]/40 hover:text-[#3b3b3b]">
                                                            Edit
                                                        </Button>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-16 bg-[#f0eff2]/30 rounded-3xl border border-dashed border-[#3b3b3b]/10">
                                        <div className="w-16 h-16 rounded-full bg-[#3b3b3b]/5 flex items-center justify-center mx-auto mb-4">
                                            <Users className="h-8 w-8 text-[#3b3b3b]/40" />
                                        </div>
                                        <h3 className="text-lg font-black text-[#3b3b3b] mb-2 uppercase tracking-tight">No contacts found</h3>
                                        <p className="text-[#3b3b3b]/60 text-sm max-w-sm mx-auto">Try adjusting your search or add a new contact to your network.</p>
                                    </div>
                                )}
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>

            {/* Modals */}
            {showNewReferralForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#3b3b3b]/20 dark:bg-black/50 backdrop-blur-sm">
                    <div className="w-full max-w-2xl max-h-[90vh] overflow-auto bg-[#f0eff2] dark:bg-[#0a0a0a] rounded-[32px] shadow-2xl p-2 relative animate-in fade-in zoom-in-95 duration-200">
                        <Button
                            className="absolute top-6 right-6 z-10 rounded-full h-8 w-8 p-0 bg-white dark:bg-[#1c1c1c] hover:bg-white dark:hover:bg-[#1c1c1c] text-[#3b3b3b] dark:text-[#f0eff2] hover:scale-110 transition-all shadow-md"
                            onClick={() => setShowNewReferralForm(false)}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                        <ReferralRequestForm
                            jobId="new-request"
                            jobTitle="General Request"
                            companyName="Target Company"
                            onSuccess={() => {
                                setShowNewReferralForm(false)
                                fetchSentReferrals()
                            }}
                        />
                    </div>
                </div>
            )}

            {/* Detailed View Modal */}
            {selectedReferral && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#3b3b3b]/20 dark:bg-black/50 backdrop-blur-sm">
                    <div className="w-full max-w-4xl max-h-[90vh] overflow-auto bg-[#f0eff2] dark:bg-[#0a0a0a] rounded-[32px] shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
                        <div className="sticky top-0 z-10 bg-[#f0eff2]/90 dark:bg-[#0a0a0a]/90 backdrop-blur-md p-6 border-b border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 flex items-center justify-between">
                            <h2 className="text-2xl font-black text-[#3b3b3b] dark:text-[#f0eff2] uppercase tracking-tight">Referral Details</h2>
                            <Button
                                className="rounded-full h-8 w-8 p-0 bg-white dark:bg-[#1c1c1c] hover:bg-white dark:hover:bg-[#1c1c1c] text-[#3b3b3b] dark:text-[#f0eff2] hover:scale-110 transition-all shadow-md"
                                onClick={() => setSelectedReferral(null)}
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </div>

                        <div className="p-8 space-y-8">
                            <div className="grid grid-cols-2 gap-8">
                                <div className="bg-white dark:bg-[#1c1c1c] p-6 rounded-3xl shadow-sm border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#3b3b3b] to-black dark:from-[#3b3b3b] dark:to-black text-white flex items-center justify-center font-black text-xl shadow-lg">
                                            {selectedReferral.contact_name.substring(0, 2)}
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold text-[#3b3b3b] dark:text-[#f0eff2]">{selectedReferral.contact_name}</h3>
                                            <p className="text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 font-medium">{selectedReferral.position} at {selectedReferral.company}</p>
                                        </div>
                                    </div>
                                    <div className="flex gap-2 pt-2">
                                        {getStatusBadge(selectedReferral.response_received ? 'responded' : 'sent')}
                                        {getRelationshipBadge(selectedReferral.contact_relationship || 'Unknown')}
                                    </div>
                                </div>

                                <div className="bg-white dark:bg-[#1c1c1c] p-6 rounded-3xl shadow-sm border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10 space-y-4">
                                    <h4 className="text-sm font-black uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40">Job Details</h4>
                                    <div>
                                        <h3 className="text-lg font-bold text-[#3b3b3b] dark:text-[#f0eff2]">{selectedReferral.job_title || 'N/A'}</h3>
                                        <p className="text-[#3b3b3b]/60 dark:text-[#f0eff2]/60 font-medium">{selectedReferral.job_company || 'N/A'}</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <Badge variant="outline" className="rounded-lg border-[#3b3b3b]/10 dark:border-[#f0eff2]/10 text-[#3b3b3b]/60 dark:text-[#f0eff2]/60">
                                            {selectedReferral.job_location || 'Remote'}
                                        </Badge>
                                        <Badge variant="outline" className="rounded-lg border-[#3b3b3b]/10 dark:border-[#f0eff2]/10 text-[#3b3b3b]/60 dark:text-[#f0eff2]/60">
                                            Job ID: {selectedReferral.job_id || 'N/A'}
                                        </Badge>
                                    </div>
                                </div>
                            </div>

                            {/* Timeline / Actions */}
                            <div className="bg-white dark:bg-[#1c1c1c] p-8 rounded-[32px] shadow-sm border border-[#3b3b3b]/5 dark:border-[#f0eff2]/10">
                                <div className="flex items-center justify-between mb-6">
                                    <h4 className="text-lg font-black text-[#3b3b3b] dark:text-[#f0eff2] uppercase tracking-tight">Timeline & Actions</h4>
                                </div>

                                <div className="relative pl-8 border-l-2 border-[#3b3b3b]/10 dark:border-[#f0eff2]/10 space-y-8">
                                    <div className="relative">
                                        <div className="absolute -left-[41px] top-1 h-5 w-5 rounded-full bg-[#f0eff2] dark:bg-[#0a0a0a] border-4 border-[#3b3b3b] dark:border-[#f0eff2]"></div>
                                        <p className="text-xs font-bold uppercase tracking-widest text-[#3b3b3b]/40 dark:text-[#f0eff2]/40 mb-1">
                                            {formatDate(selectedReferral.sent_at)}
                                        </p>
                                        <p className="font-medium text-[#3b3b3b] dark:text-[#f0eff2]">Referral Request Sent</p>
                                    </div>

                                    {selectedReferral.response_received ? (
                                        <div className="relative">
                                            <div className="absolute -left-[41px] top-1 h-5 w-5 rounded-full bg-emerald-100 border-4 border-emerald-500"></div>
                                            <p className="text-xs font-bold uppercase tracking-widest text-emerald-600 mb-1">
                                                {selectedReferral.response_date ? formatDate(selectedReferral.response_date) : 'Responded'}
                                            </p>
                                            <p className="font-medium text-[#3b3b3b] dark:text-[#f0eff2]">Response Received</p>
                                        </div>
                                    ) : (
                                        <div className="relative">
                                            <div className="absolute -left-[41px] top-0 h-5 w-5 rounded-full bg-white dark:bg-black/20 border-4 border-[#3b3b3b]/20 dark:border-[#f0eff2]/20"></div>
                                            <Button
                                                onClick={() => markResponseReceived(selectedReferral.sent_id)}
                                                className="bg-[#3b3b3b] dark:bg-white hover:bg-black dark:hover:bg-[#e5e5e5] text-white dark:text-black rounded-xl text-xs font-bold uppercase tracking-widest px-6"
                                            >
                                                Mark Response Received
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}