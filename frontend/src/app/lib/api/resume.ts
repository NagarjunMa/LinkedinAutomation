import { ResumeFile, ResumeEvaluation, ResumeListItemResponse } from './types';
import { makeAPIRequest, getAuthHeaders } from './config';

export const resumeApi = {
    // Upload resume
    uploadResume: async (file: File, targetRole?: string, targetSeniority?: string): Promise<ResumeFile> => {
        const formData = new FormData();
        formData.append('file', file);
        if (targetRole) formData.append('target_role', targetRole);
        if (targetSeniority) formData.append('target_seniority', targetSeniority);

        const authHeaders = await getAuthHeaders();
        // Remove Content-Type to let browser set it with boundary for FormData
        if (authHeaders['Content-Type']) {
            delete authHeaders['Content-Type'];
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/resumes/upload`, {
            method: 'POST',
            headers: authHeaders,
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to upload resume');
        }

        const data = await response.json();
        const resumeId = data.resume_document_id || data.id;
        return {
            id: resumeId,
            filename: data.original_filename || file.name,
            original_filename: data.original_filename || file.name,
            file_size: data.file_size || file.size,
            file_type: data.file_type || file.name.split('.').pop() || 'unknown',
            uploaded_at: data.uploaded_at || new Date().toISOString(),
            evaluation_status: data.evaluation_status || 'pending',
        };
    },

    // Evaluate resume
    evaluateResume: async (resumeId: string, targetRole?: string, targetSeniority?: string): Promise<{ message: string, process_id: string, status: string }> => {
        const url = `/api/v1/resumes/${resumeId}/evaluate`;
        const data = await makeAPIRequest<{ message: string, process_id: string, status: string }>(url, {
            method: 'POST',
            body: JSON.stringify({
                resume_id: resumeId,
                target_role: targetRole || null,
                target_seniority: targetSeniority || null
            })
        });

        return data;
    },

    getEvaluationProgress: async (resumeId: string): Promise<{
        resume_id: string
        evaluation_status: string
        progress: {
            status: string
            started_at: string
            stages: Record<string, {
                status: 'pending' | 'running' | 'completed' | 'failed'
                started_at: string | null
                completed_at: string | null
            }>
            overall_progress: number
        }
    }> => {
        const url = `/api/v1/resumes/${resumeId}/evaluation-progress`;
        return makeAPIRequest(url, { method: 'GET' });
    },

    // List resumes
    listResumes: async (): Promise<{ resumes: ResumeFile[]; totalCount: number }> => {
        const url = '/api/v1/resumes/list';
        const data = await makeAPIRequest<{ resumes: ResumeListItemResponse[], total_count: number, totalCount: number }>(url);

        // For each resume, fetch the detailed evaluation if status is completed
        const resumesWithEvaluations = await Promise.all(
            (Array.isArray(data.resumes) ? data.resumes : [] as ResumeListItemResponse[]).map(async (r: ResumeListItemResponse) => {
                const baseResume: ResumeFile = {
                    id: r.id,
                    filename: r.original_filename || r.filename || 'Untitled Resume',
                    original_filename: r.original_filename || r.filename || 'Untitled Resume',
                    file_size: r.file_size || r.size || 0,
                    file_type: r.file_type || r.type || 'unknown',
                    uploaded_at: r.uploaded_at || r.uploadedAt || new Date().toISOString(),
                    evaluation_status: (r.evaluation_status || r.evaluationStatus || 'pending') as 'pending' | 'completed' | 'failed' | 'evaluating',
                    evaluation_result: undefined,
                };

                // If evaluation is completed, fetch the detailed results
                if (baseResume.evaluation_status === 'completed') {
                    try {
                        const detailedData = await makeAPIRequest<{ evaluation: ResumeEvaluation }>(`/api/v1/resumes/${r.id}`);
                        if (detailedData.evaluation) {
                            baseResume.evaluation_result = {
                                id: detailedData.evaluation.id || r.id, // Fallback to resume ID if evaluation ID missing
                                resume_id: detailedData.evaluation.resume_id || r.id,
                                overall_score: detailedData.evaluation.overall_score,
                                ai_score: detailedData.evaluation.ai_score,
                                ats_compliance_score: detailedData.evaluation.ats_compliance_score,
                                ats_score: detailedData.evaluation.ats_score,
                                content_quality_score: detailedData.evaluation.content_quality_score,
                                experience_points_score: detailedData.evaluation.experience_points_score,
                                job_relevance_score: detailedData.evaluation.job_relevance_score,
                                quality_checks_score: detailedData.evaluation.quality_checks_score,
                                strengths: detailedData.evaluation.strengths || [],
                                optical_strengths: detailedData.evaluation.optical_strengths || [],
                                improvements: detailedData.evaluation.improvements || [],
                                strategic_improvements: detailedData.evaluation.strategic_improvements || [],
                                ats_compatibility: detailedData.evaluation.ats_compatibility,
                                ats_compatibility_details: detailedData.evaluation.ats_compatibility_details,
                                detailed_feedback: detailedData.evaluation.detailed_feedback,
                                keyword_analysis: detailedData.evaluation.keyword_analysis || { relevant: [], missing: [], score: 0 },
                                critical_issues: detailedData.evaluation.critical_issues,
                                market_positioning: detailedData.evaluation.market_positioning,
                                wording_suggestions: detailedData.evaluation.wording_suggestions,
                                evaluation_metadata: detailedData.evaluation.evaluation_metadata,
                            };
                        }
                    } catch (error) {
                        console.error(`Failed to fetch evaluation for resume ${r.id}:`, error);
                    }
                }

                return baseResume;
            })
        );

        return {
            resumes: resumesWithEvaluations,
            totalCount: data.total_count || data.totalCount || 0,
        };
    },

    // Get resume with evaluation
    getResume: async (resumeId: string): Promise<ResumeFile & { evaluationResult?: ResumeEvaluation }> => {
        const url = `/api/v1/resumes/${resumeId}`;
        const data = await makeAPIRequest<{ resume: any, evaluation?: ResumeEvaluation }>(url);

        return {
            id: data.resume.id,
            filename: data.resume.original_filename,
            original_filename: data.resume.original_filename,
            file_size: data.resume.file_size,
            file_type: data.resume.file_type,
            uploaded_at: data.resume.uploaded_at,
            evaluation_status: data.resume.evaluation_status,
            evaluation_result: data.evaluation ? {
                id: data.evaluation.id || resumeId,
                resume_id: data.evaluation.resume_id || resumeId,
                overall_score: data.evaluation.overall_score,
                ai_score: data.evaluation.ai_score,
                ats_compliance_score: data.evaluation.ats_compliance_score,
                ats_score: data.evaluation.ats_score,
                content_quality_score: data.evaluation.content_quality_score,
                experience_points_score: data.evaluation.experience_points_score,
                job_relevance_score: data.evaluation.job_relevance_score,
                quality_checks_score: data.evaluation.quality_checks_score,
                strengths: data.evaluation.strengths || [],
                optical_strengths: data.evaluation.optical_strengths || [],
                improvements: data.evaluation.improvements || [],
                strategic_improvements: data.evaluation.strategic_improvements || [],
                ats_compatibility: data.evaluation.ats_compatibility,
                ats_compatibility_details: data.evaluation.ats_compatibility_details,
                detailed_feedback: data.evaluation.detailed_feedback,
                keyword_analysis: data.evaluation.keyword_analysis || { relevant: [], missing: [], score: 0 },
                critical_issues: data.evaluation.critical_issues,
                market_positioning: data.evaluation.market_positioning,
                wording_suggestions: data.evaluation.wording_suggestions,
                evaluation_metadata: data.evaluation.evaluation_metadata,
            } : undefined,
        };
    },

    // Delete resume
    deleteResume: async (resumeId: string): Promise<void> => {
        const url = `/api/v1/resumes/${resumeId}`;
        await makeAPIRequest(url, { method: 'DELETE' });
    },

    // Get storage info
    getStorageInfo: async (): Promise<{ totalCount: number; storageUsed: number; storageLimit: number }> => {
        const url = '/api/v1/resumes/storage-info';
        const data = await makeAPIRequest<{ total_count: number; storage_used: number; storage_limit: number }>(url);

        return {
            totalCount: data.total_count,
            storageUsed: data.storage_used,
            storageLimit: data.storage_limit,
        };
    },
};
