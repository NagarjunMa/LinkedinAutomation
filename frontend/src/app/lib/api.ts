

export async function fetchJobs() {

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${API_URL}/api/v1/jobs/`);
    if (!response.ok) {
        throw new Error("Failed to fetch jobs");
    }
    const data = await response.json();
    // Map backend fields to frontend fields
    return data.map((job: any) => ({
        id: job.id,
        title: job.title,
        company: job.company,
        location: job.location,
        type: job.job_type, // map job_type to type
        description: job.description,
        url: job.application_url, // map application_url to url
        postedAt: job.posted_date, // map posted_date to postedAt
        salary: job.salary_range,
        experience: job.experience_level,
        skills: job.skills || [],
    }));
}