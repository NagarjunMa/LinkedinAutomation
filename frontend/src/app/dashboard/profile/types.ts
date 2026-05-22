export interface JobPreferences {
    roles: string[];
    locations: string[];
    salaryRange: string;
}

export interface ResumeVersion {
    id: string;
    fileName: string;
    uploadDate: string;
    score: number;
    isActive: boolean;
}

export interface UserStats {
    applications: number;
    experiences: number;
}

export interface ProfileData {
    user: {
        name: string;
        email: string;
        location: string;
        title: string;
    };
    stats: UserStats;
    resumes: ResumeVersion[];
    preferences: JobPreferences;
    /** @deprecated kept for API shape compat; not displayed in UI */
    referralBlueprint?: string;
}
