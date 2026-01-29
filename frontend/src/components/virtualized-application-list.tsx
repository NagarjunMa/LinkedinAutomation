"use client"

import { memo, forwardRef } from 'react'
import { FixedSizeList } from 'react-window'
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
    const baseClasses = "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border shadow-sm";

    switch (status) {
        case 'applied':
            return <Badge className={`${baseClasses} bg-green-50 text-green-600 border-green-200`}><CheckCircle className="w-3 h-3 mr-1" />Applied</Badge>
        case 'interview_scheduled':
            return <Badge className={`${baseClasses} bg-blue-50 text-blue-600 border-blue-200`}><Calendar className="w-3 h-3 mr-1" />Interview</Badge>
        case 'want_to_apply':
            return <Badge className={`${baseClasses} bg-yellow-50 text-yellow-600 border-yellow-200`}><Target className="w-3 h-3 mr-1" />Want to Apply</Badge>
        case 'not_interested':
            return <Badge className={`${baseClasses} bg-red-50 text-red-600 border-red-200`}><X className="w-3 h-3 mr-1" />Not Interested</Badge>
        default:
            return <Badge className={`${baseClasses} bg-gray-50 text-gray-600 border-gray-200`}><Clock className="w-3 h-3 mr-1" />Pending</Badge>
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
                    <Card className="hover:shadow-lg transition-shadow animate-pulse bg-white rounded-[32px] border border-[#3b3b3b]/5">
                        <CardContent className="p-6">
                            <div className="h-20 bg-[#f0eff2] rounded-xl"></div>
                        </CardContent>
                    </Card>
                </div>
            );
        }

        return (
            <div ref={ref} style={style} className="p-2">
                <Card className="group bg-white rounded-[32px] border border-[#3b3b3b]/5 shadow-sm hover:shadow-xl transition-all hover:border-[#3b3b3b]/20">
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <h3 className="text-lg font-bold text-[#3b3b3b]">
                                        {application.title}
                                    </h3>
                                    {getStatusBadge(application.status)}
                                </div>

                                <div className="flex items-center gap-4 text-sm text-[#3b3b3b]/60 mb-3 font-medium">
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

                                <div className="flex items-center gap-4 text-xs font-bold uppercase tracking-wider text-[#3b3b3b]/40 mb-3">
                                    <div className="flex items-center gap-1">
                                        <Calendar className="w-3 h-3" />
                                        <span>Applied: {application.appliedDate || 'Not applied'}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <TrendingUp className="w-3 h-3" />
                                        <span>{application.compatibilityScore}% match</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Users className="w-3 h-3" />
                                        <span>Source: {application.source}</span>
                                    </div>
                                </div>

                                {application.extractedAt && (
                                    <div className="text-[10px] uppercase tracking-widest text-[#3b3b3b]/30 mb-2 font-black">
                                        Extracted: {new Date(application.extractedAt).toLocaleDateString()}
                                    </div>
                                )}

                                {application.notes && (
                                    <div className="text-sm text-[#3b3b3b]/70 bg-[#f0eff2] p-3 rounded-xl mt-2 border border-[#3b3b3b]/5">
                                        <strong>Notes:</strong> {application.notes}
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-2 ml-4">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onViewDetails(application)}
                                    className="px-4 py-2 bg-white border border-[#3b3b3b]/10 rounded-xl font-bold text-xs uppercase tracking-wider text-[#3b3b3b] hover:bg-[#f0eff2] transition-all"
                                >
                                    View Details
                                </Button>
                                {application.sourceUrl && (
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => onViewJob(application.sourceUrl!)}
                                        className="px-4 py-2 bg-white border border-blue-200 rounded-xl font-bold text-xs uppercase tracking-wider text-blue-600 hover:bg-blue-50 transition-all"
                                    >
                                        <ExternalLink className="w-3 h-3 mr-1" />
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
            <FixedSizeList
                height={height}
                itemCount={applications.length}
                itemSize={itemHeight}
                itemData={itemData}
                overscanCount={5} // Render 5 extra items for smooth scrolling
            >
                {ApplicationItem}
            </FixedSizeList>
        </div>
    );
});

export default VirtualizedApplicationList;