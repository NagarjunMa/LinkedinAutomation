"use client"

import { memo, forwardRef } from 'react'
import { FixedSizeList as List } from 'react-window'
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
    ExternalLink,
    CheckCircle,
    Clock,
    X,
    Target,
    Briefcase,
    Calendar,
    MapPin,
    DollarSign,
    Users,
    TrendingUp
} from "lucide-react"

type ApplicationStatus = 'applied' | 'interview_scheduled' | 'want_to_apply' | 'not_interested' | string

interface Application {
    id: string;
    title: string;
    company: string;
    location: string;
    salary: string;
    status: ApplicationStatus;
    appliedDate: string | null;
    source: string;
    compatibilityScore: number;
    notes: string;
    sourceUrl?: string;
    extractedAt?: string;
}

interface ApplicationItemProps {
    index: number;
    style: React.CSSProperties;
    data: {
        applications: Application[];
        getStatusBadge: (status: ApplicationStatus) => React.ReactNode;
        onViewJob: (url: string) => void;
        onViewDetails: (application: Application) => void;
    };
}

const getStatusBadge = (status: ApplicationStatus) => {
    switch (status) {
        case 'applied':
            return <Badge className="bg-green-500 text-white"><CheckCircle className="w-3 h-3 mr-1" />Applied</Badge>
        case 'interview_scheduled':
            return <Badge className="bg-blue-500 text-white"><Calendar className="w-3 h-3 mr-1" />Interview</Badge>
        case 'want_to_apply':
            return <Badge className="bg-yellow-500 text-black"><Target className="w-3 h-3 mr-1" />Want to Apply</Badge>
        case 'not_interested':
            return <Badge className="bg-gray-500 text-white"><X className="w-3 h-3 mr-1" />Not Interested</Badge>
        default:
            return <Badge className="bg-orange-500 text-white"><Clock className="w-3 h-3 mr-1" />Pending</Badge>
    }
}

// Virtualized application item component
const ApplicationItem = memo(forwardRef<HTMLDivElement, ApplicationItemProps>(
    function ApplicationItem({ index, style, data }, ref) {
        const { applications, onViewJob, onViewDetails } = data;
        const application = applications[index];

        if (!application) {
            return (
                <div ref={ref} style={style} className="p-2">
                    <Card className="hover:shadow-lg transition-shadow animate-pulse">
                        <CardContent className="p-4">
                            <div className="h-20 bg-gray-300 rounded"></div>
                        </CardContent>
                    </Card>
                </div>
            );
        }

        return (
            <div ref={ref} style={style} className="p-2">
                <Card className="hover:shadow-lg transition-shadow">
                    <CardContent className="p-4 sm:p-6">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <h3 className="text-xl font-semibold text-cream-50">
                                        {application.title}
                                    </h3>
                                    {getStatusBadge(application.status)}
                                </div>

                                <div className="flex items-center gap-4 text-sm text-cream-300 mb-3">
                                    <div className="flex items-center gap-1">
                                        <Briefcase className="w-4 h-4" />
                                        <span>{application.company}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <MapPin className="w-4 h-4" />
                                        <span>{application.location}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <DollarSign className="w-4 h-4" />
                                        <span>{application.salary}</span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4 text-sm text-cream-400 mb-3">
                                    <div className="flex items-center gap-1">
                                        <Calendar className="w-4 h-4" />
                                        <span>Applied: {application.appliedDate || 'Not applied'}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <TrendingUp className="w-4 h-4" />
                                        <span>{application.compatibilityScore}% match</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Users className="w-4 h-4" />
                                        <span>Source: {application.source}</span>
                                    </div>
                                </div>

                                {application.extractedAt && (
                                    <div className="text-xs text-cream-500 mb-2">
                                        Extracted: {new Date(application.extractedAt).toLocaleDateString()}
                                    </div>
                                )}

                                {application.notes && (
                                    <div className="text-sm text-cream-300 bg-cream-900 p-2 rounded mt-2">
                                        <strong>Notes:</strong> {application.notes}
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-2 ml-4">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onViewDetails(application)}
                                    className="text-cream-300 border-cream-600 hover:bg-cream-800"
                                >
                                    View Details
                                </Button>
                                {application.sourceUrl && (
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => onViewJob(application.sourceUrl!)}
                                        className="text-blue-400 border-blue-600 hover:bg-blue-900"
                                    >
                                        <ExternalLink className="w-4 h-4 mr-1" />
                                        View Job
                                    </Button>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }
));

interface VirtualizedApplicationListProps {
    applications: Application[];
    onViewJob: (url: string) => void;
    onViewDetails: (application: Application) => void;
    height?: number;
}

export const VirtualizedApplicationList = memo(function VirtualizedApplicationList({
    applications,
    onViewJob,
    onViewDetails,
    height = 600
}: VirtualizedApplicationListProps) {
    const itemData = {
        applications,
        getStatusBadge,
        onViewJob,
        onViewDetails
    };

    // Calculate item height: base height + padding + margins
    const itemHeight = 200; // Approximate height per application card

    return (
        <div className="border rounded-lg overflow-hidden">
            <List
                height={height}
                itemCount={applications.length}
                itemSize={itemHeight}
                itemData={itemData}
                overscanCount={5} // Render 5 extra items for smooth scrolling
            >
                {ApplicationItem}
            </List>
        </div>
    );
});

export default VirtualizedApplicationList;