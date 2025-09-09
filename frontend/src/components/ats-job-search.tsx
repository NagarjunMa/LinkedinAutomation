"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { Search, ExternalLink, Plus, Copy, Check, Upload } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

// ATS Platform configurations with optimized site paths for maximum job discovery
const ATS_PLATFORMS = [
    { name: "Greenhouse", site: "greenhouse.io" },
    { name: "Lever", site: "lever.co" },
    { name: "Ashby", site: "ashbyhq.com" },
    { name: "Remote Rocketship", site: "remoterocketship.com" },
    { name: "Jobs Subdomain", site: "jobs.*" },
    { name: "Careers Pages", site: "careers.*" },
    { name: "Talent Subdomain", site: "talent.*" },
    { name: "Paylocity", site: "paylocity.com" },
    { name: "Keka", site: "keka.com" },
    { name: "Workable", site: "apply.workable.com" },
    { name: "BreezyHR", site: "breezy.hr" },
    { name: "Wellfound", site: "wellfound.com" },
    { name: "Y Combinator Work at a Startup", site: "ycombinator.com" },
    { name: "Oracle Cloud", site: "oracle.com" },
    { name: "Workday Jobs", site: "workday.com" },
    { name: "Recruitee", site: "recruitee.com" },
    { name: "Rippling", site: "rippling.com" },
    { name: "Gusto", site: "gusto.com" },
    { name: "CareerPuck", site: "careerpuck.com" },
    { name: "Teamtailor", site: "teamtailor.com" },
    { name: "SmartRecruiters", site: "smartrecruiters.com" },
    { name: "TalentReef", site: "talentreef.com" },
    { name: "Homerun", site: "homerun.co" },
    { name: "Gem", site: "gem.com" },
    { name: "Trakstar", site: "trakstar.com" },
    { name: "Cats", site: "catsone.com" },
    { name: "JazzHR", site: "jazzhr.com" },
    { name: "Jobvite", site: "jobvite.com" },
    { name: "iCIMS", site: "icims.com" },
    { name: "Dover", site: "dover.io" },
    { name: "Notion", site: "notion.so" },
    { name: "Builtin", site: "builtin.com" },
    { name: "ADP", site: "adp.com" },
    { name: "LinkedIn", site: "linkedin.com/jobs" },
    { name: "Glassdoor", site: "glassdoor.com/job-listing" },
    { name: "TriNet Hire", site: "trinet.com" },
    { name: "Other Pages", site: "*" }
]

// Timeframe options
const TIMEFRAME_OPTIONS = [
    { value: "h1", label: "Past Hour" },
    { value: "h4", label: "Past 4 Hours" },
    { value: "h8", label: "Past 8 Hours" },
    { value: "h12", label: "Past 12 Hours" },
    { value: "d1", label: "Past 24 Hours" },
    { value: "d2", label: "Past 48 Hours" },
    { value: "d3", label: "Past 72 Hours" },
    { value: "w1", label: "Past Week" },
    { value: "m1", label: "Past Month" }
]


interface SearchForm {
    jobTitle: string
    locations: string[]
    timeframe: string
    atsPlatforms: string[]
}

interface GeneratedQuery {
    url: string
    platform: string
    copied: boolean
}

export function ATSJobSearch() {
    const [form, setForm] = useState<SearchForm>({
        jobTitle: "",
        locations: [],
        timeframe: "h4",
        atsPlatforms: []
    })

    const [currentLocation, setCurrentLocation] = useState("")
    const [generatedQueries, setGeneratedQueries] = useState<GeneratedQuery[]>([])
    const [isGenerating, setIsGenerating] = useState(false)
    const [urlImportText, setUrlImportText] = useState("")
    const [isImporting, setIsImporting] = useState(false)
    const { toast } = useToast()

    // Generate Google search URLs for selected ATS platforms
    const generateSearchQueries = () => {
        if (!form.jobTitle.trim()) {
            toast({
                title: "Error",
                description: "Please enter a job title",
                variant: "destructive"
            })
            return
        }

        if (form.atsPlatforms.length === 0) {
            toast({
                title: "Error",
                description: "Please select at least one ATS platform",
                variant: "destructive"
            })
            return
        }

        setIsGenerating(true)

        const queries: GeneratedQuery[] = []

        form.atsPlatforms.forEach(platformName => {
            const platform = ATS_PLATFORMS.find(p => p.name === platformName)
            if (!platform) return

            let searchUrl: string

            // Handle special cases with direct URLs instead of Google search
            if (platformName === "Remote Rocketship") {
                // Build direct Remote Rocketship URL
                const params = new URLSearchParams({
                    ref: 'briansjobsearch',
                    jobTitle: form.jobTitle,
                    page: '1',
                    sort: 'DateAdded'
                })
                searchUrl = `https://www.remoterocketship.com/?${params.toString()}`
            } else {
                // Build the search query in optimal order for Google search
                let query = `"${form.jobTitle}"`

                // Handle special site patterns for comprehensive searches
                if (platformName === "Careers Pages") {
                    // Use comprehensive careers page search pattern
                    query += ` (site:careers.* OR site:*/careers/* OR site:*/career/*)`
                } else {
                    // Add site restriction first (for better targeting)
                    query += ` site:${platform.site}`
                }

                // Add location if specified
                if (form.locations.length > 0) {
                    const locationQuery = form.locations.join(" OR ")
                    query += ` (${locationQuery})`
                } else {
                    // Add remote keyword at the end for better results
                    query += " remote"
                }

                // Build the complete Google search URL
                searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}&tbs=qdr:${form.timeframe}`
            }

            queries.push({
                url: searchUrl,
                platform: platformName,
                copied: false
            })
        })

        setGeneratedQueries(queries)
        setIsGenerating(false)

        toast({
            title: "Success",
            description: `Generated ${queries.length} search queries`
        })
    }

    // Open search results in new tabs
    const openAllSearches = () => {
        if (generatedQueries.length === 0) {
            toast({
                title: "Error",
                description: "No search queries generated yet",
                variant: "destructive"
            })
            return
        }

        generatedQueries.forEach(query => {
            window.open(query.url, '_blank')
        })

        toast({
            title: "Success",
            description: `Opened ${generatedQueries.length} search tabs`
        })
    }

    // Copy URL to clipboard
    const copyUrl = async (index: number) => {
        try {
            await navigator.clipboard.writeText(generatedQueries[index].url)

            setGeneratedQueries(prev =>
                prev.map((query, i) =>
                    i === index ? { ...query, copied: true } : query
                )
            )

            // Reset copied state after 2 seconds
            setTimeout(() => {
                setGeneratedQueries(prev =>
                    prev.map((query, i) =>
                        i === index ? { ...query, copied: false } : query
                    )
                )
            }, 2000)

            toast({
                title: "Copied",
                description: "URL copied to clipboard"
            })
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to copy URL",
                variant: "destructive"
            })
        }
    }

    // Add location to the list
    const addLocation = () => {
        if (currentLocation.trim() && !form.locations.includes(currentLocation.trim())) {
            setForm(prev => ({
                ...prev,
                locations: [...prev.locations, currentLocation.trim()]
            }))
            setCurrentLocation("")
        }
    }

    // Remove location from the list
    const removeLocation = (location: string) => {
        setForm(prev => ({
            ...prev,
            locations: prev.locations.filter(l => l !== location)
        }))
    }

    // Toggle ATS platform selection
    const toggleATSPlatform = (platform: string) => {
        setForm(prev => ({
            ...prev,
            atsPlatforms: prev.atsPlatforms.includes(platform)
                ? prev.atsPlatforms.filter(p => p !== platform)
                : [...prev.atsPlatforms, platform]
        }))
    }

    // Import job URLs to the main tracking system
    const importJobUrls = async () => {
        if (!urlImportText.trim()) {
            toast({
                title: "Error",
                description: "Please enter job URLs to import",
                variant: "destructive"
            })
            return
        }

        setIsImporting(true)

        try {
            // Parse URLs from the textarea (one per line)
            const urls = urlImportText
                .split('\n')
                .map(url => url.trim())
                .filter(url => url && isValidUrl(url))

            if (urls.length === 0) {
                toast({
                    title: "Error",
                    description: "No valid URLs found. Please check your input.",
                    variant: "destructive"
                })
                return
            }

            // Import each URL to the job tracking system
            const importPromises = urls.map(url => importJobUrl(url))
            await Promise.all(importPromises)

            toast({
                title: "Success",
                description: `Successfully imported ${urls.length} job URLs`
            })

            // Clear the textarea
            setUrlImportText("")
        } catch (error) {
            console.error('Failed to import URLs:', error)
            toast({
                title: "Error",
                description: "Failed to import some URLs. Please try again.",
                variant: "destructive"
            })
        } finally {
            setIsImporting(false)
        }
    }

    // Helper function to validate URLs
    const isValidUrl = (string: string): boolean => {
        try {
            new URL(string)
            return true
        } catch (_) {
            return false
        }
    }

    // Import a single job URL
    const importJobUrl = async (url: string) => {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        const response = await fetch(`${API_BASE_URL}/api/v1/jobs/import-url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                source: 'ats_search_import'
            }),
        })

        if (!response.ok) {
            throw new Error(`Failed to import URL: ${url}`)
        }

        return response.json()
    }

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold">Advanced Job Search</h2>
                <p className="text-muted-foreground">
                    Search across multiple job platforms with optimized queries
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Search Configuration */}
                <Card>
                    <CardHeader>
                        <CardTitle>Search Configuration</CardTitle>
                        <CardDescription>
                            Configure your job search parameters
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Job Title */}
                        <div className="space-y-2">
                            <Label htmlFor="jobTitle">Job Title *</Label>
                            <Input
                                id="jobTitle"
                                placeholder="e.g., Backend Engineer, Product Manager"
                                value={form.jobTitle}
                                onChange={(e) => setForm(prev => ({ ...prev, jobTitle: e.target.value }))}
                            />
                        </div>

                        {/* Locations */}
                        <div className="space-y-2">
                            <Label>Locations (Optional)</Label>
                            <div className="flex gap-2">
                                <Input
                                    placeholder="e.g., San Francisco, Remote, New York"
                                    value={currentLocation}
                                    onChange={(e) => setCurrentLocation(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && addLocation()}
                                />
                                <Button onClick={addLocation} size="sm">
                                    <Plus className="h-4 w-4" />
                                </Button>
                            </div>
                            {form.locations.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    {form.locations.map((location) => (
                                        <Badge
                                            key={location}
                                            variant="secondary"
                                            className="cursor-pointer"
                                            onClick={() => removeLocation(location)}
                                        >
                                            {location} ×
                                        </Badge>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Timeframe */}
                        <div className="space-y-2">
                            <Label htmlFor="timeframe">Timeframe</Label>
                            <Select
                                value={form.timeframe}
                                onValueChange={(value) => setForm(prev => ({ ...prev, timeframe: value }))}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {TIMEFRAME_OPTIONS.map((option) => (
                                        <SelectItem key={option.value} value={option.value}>
                                            {option.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* ATS Platforms */}
                        <div className="space-y-2">
                            <Label>ATS Platforms *</Label>
                            <div className="max-h-48 overflow-y-auto border rounded-md p-3 space-y-2">
                                {ATS_PLATFORMS.map((platform) => (
                                    <label key={platform.name} className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={form.atsPlatforms.includes(platform.name)}
                                            onChange={() => toggleATSPlatform(platform.name)}
                                            className="rounded"
                                        />
                                        <span className="text-sm">{platform.name}</span>
                                    </label>
                                ))}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Selected: {form.atsPlatforms.length} platforms
                            </p>
                        </div>

                        {/* Generate Button */}
                        <Button
                            onClick={generateSearchQueries}
                            disabled={isGenerating}
                            className="w-full"
                        >
                            <Search className="h-4 w-4 mr-2" />
                            {isGenerating ? "Generating..." : "Generate Search Queries"}
                        </Button>
                    </CardContent>
                </Card>

                {/* Generated Queries */}
                <Card>
                    <CardHeader>
                        <CardTitle>Generated Search Queries</CardTitle>
                        <CardDescription>
                            {generatedQueries.length > 0
                                ? `${generatedQueries.length} queries ready to open`
                                : "Generate queries to see results here"
                            }
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {generatedQueries.length > 0 && (
                            <div className="space-y-3">
                                <Button
                                    onClick={openAllSearches}
                                    className="w-full"
                                    variant="outline"
                                >
                                    <ExternalLink className="h-4 w-4 mr-2" />
                                    Open All Searches in New Tabs
                                </Button>

                                <div className="space-y-2 max-h-96 overflow-y-auto">
                                    {generatedQueries.map((query, index) => (
                                        <div key={index} className="border rounded-lg p-3 space-y-2">
                                            <div className="flex items-center justify-between">
                                                <Badge variant="outline">{query.platform}</Badge>
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() => copyUrl(index)}
                                                >
                                                    {query.copied ? (
                                                        <Check className="h-4 w-4 text-green-600" />
                                                    ) : (
                                                        <Copy className="h-4 w-4" />
                                                    )}
                                                </Button>
                                            </div>
                                            <div className="text-xs text-muted-foreground break-all">
                                                {query.url}
                                            </div>
                                            <div className="text-xs text-blue-600 font-mono bg-blue-50 p-2 rounded mt-1">
                                                Query: {decodeURIComponent(query.url.split('q=')[1]?.split('&')[0] || '')}
                                            </div>
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => window.open(query.url, '_blank')}
                                                className="w-full"
                                            >
                                                <ExternalLink className="h-3 w-3 mr-1" />
                                                Open Search
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {generatedQueries.length === 0 && (
                            <div className="text-center py-8 text-muted-foreground">
                                <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>No search queries generated yet</p>
                                <p className="text-sm">Configure your search and click "Generate Search Queries"</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>


            {/* URL Import Section */}
            {generatedQueries.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Import Job URLs</CardTitle>
                        <CardDescription>
                            Found relevant jobs? Import their URLs to track them in your main job tracking system
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <Textarea
                                placeholder="Paste job URLs here (one per line)..."
                                className="min-h-24"
                                value={urlImportText}
                                onChange={(e) => setUrlImportText(e.target.value)}
                            />
                            <div className="flex gap-2">
                                <Button
                                    onClick={importJobUrls}
                                    disabled={isImporting || !urlImportText.trim()}
                                >
                                    <Upload className="h-4 w-4 mr-2" />
                                    {isImporting ? "Importing..." : "Import URLs"}
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => setUrlImportText("")}
                                    disabled={!urlImportText.trim()}
                                >
                                    Clear
                                </Button>
                            </div>
                            {urlImportText.trim() && (
                                <div className="text-sm text-muted-foreground">
                                    {urlImportText.split('\n').filter(url => url.trim()).length} URLs ready to import
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
