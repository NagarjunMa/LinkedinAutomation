"use client"

import React, { useState } from "react";

const jobTypes = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"];
const experienceLevels = ["Entry Level", "Associate", "Mid-Senior Level", "Director", "Executive"];
const schedules = ["Morning", "Afternoon", "Evening", "Night", "Weekend"];
const postedWithinOptions = ["24 hours", "3 days", "1 week", "2 weeks", "1 month"];

export function JobSearchForm() {

    const [searchParams, setSearchParams] = useState({
        keywords: "",
        location: "",
        jobType: "",
        experienceLevel: "",
        schedule: "",
        remote: false,
        postedWithin: "",
    });

    function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
        const { name, value, type } = e.target;
        setSearchParams((prev) => ({
            ...prev,
            [name]: type === "checkbox"
                ? (e.target as HTMLInputElement).checked
                : value,
        }));
    }

    function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        // Add your search logic here
    }

    return (
        <div className="bg-white text-black rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-6 text-primary">Search Jobs</h2>
            <form className="space-y-6" onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                        <label htmlFor="keywords" className="font-semibold text-gray-700">Keywords</label>
                        <input
                            id="keywords"
                            name="keywords"
                            placeholder="Job title, skills, or company"
                            className="bg-gray-50 focus:bg-white rounded px-3 py-2 w-full border border-gray-300 focus:border-blue-500 outline-none"
                            value={searchParams.keywords}
                            onChange={handleChange}
                        />
                    </div>
                    <div className="space-y-1.5">
                        <label htmlFor="location" className="font-semibold text-gray-700">Location</label>
                        <input
                            id="location"
                            name="location"
                            placeholder="City, state, or remote"
                            className="bg-gray-50 focus:bg-white rounded px-3 py-2 w-full border border-gray-300 focus:border-blue-500 outline-none"
                            value={searchParams.location}
                            onChange={handleChange}
                        />
                    </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="space-y-1.5">
                        <label htmlFor="jobType" className="font-semibold text-gray-700">Job Type</label>
                        <select
                            id="jobType"
                            name="jobType"
                            className="bg-gray-50 focus:bg-white rounded px-3 py-2 w-full border border-gray-300 focus:border-blue-500 outline-none"
                            value={searchParams.jobType}
                            onChange={handleChange}
                        >
                            <option value="">Select job type</option>
                            {jobTypes.map((type) => (
                                <option key={type} value={type}>{type}</option>
                            ))}
                        </select>
                    </div>
                    <div className="space-y-1.5">
                        <label htmlFor="experienceLevel" className="font-semibold text-gray-700">Experience Level</label>
                        <select
                            id="experienceLevel"
                            name="experienceLevel"
                            className="bg-gray-50 focus:bg-white rounded px-3 py-2 w-full border border-gray-300 focus:border-blue-500 outline-none"
                            value={searchParams.experienceLevel}
                            onChange={handleChange}
                        >
                            <option value="">Select experience level</option>
                            {experienceLevels.map((level) => (
                                <option key={level} value={level}>{level}</option>
                            ))}
                        </select>
                    </div>
                    <div className="space-y-1.5">
                        <label htmlFor="schedule" className="font-semibold text-gray-700">Schedule</label>
                        <select
                            id="schedule"
                            name="schedule"
                            className="bg-gray-50 focus:bg-white rounded px-3 py-2 w-full border border-gray-300 focus:border-blue-500 outline-none"
                            value={searchParams.schedule}
                            onChange={handleChange}
                        >
                            <option value="">Select schedule</option>
                            {schedules.map((schedule) => (
                                <option key={schedule} value={schedule}>{schedule}</option>
                            ))}
                        </select>
                    </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-1.5">
                        <label htmlFor="postedWithin" className="font-semibold text-gray-700">Posted Within</label>
                        <select
                            id="postedWithin"
                            name="postedWithin"
                            className="bg-gray-50 focus:bg-white rounded px-3 py-2 w-full border border-gray-300 focus:border-blue-500 outline-none"
                            value={searchParams.postedWithin}
                            onChange={handleChange}
                        >
                            <option value="">Select time range</option>
                            {postedWithinOptions.map((option) => (
                                <option key={option} value={option}>{option}</option>
                            ))}
                        </select>
                    </div>
                    <div className="flex items-center gap-3 mt-6 md:mt-0">
                        <input
                            type="checkbox"
                            id="remote"
                            name="remote"
                            checked={searchParams.remote}
                            onChange={handleChange}
                            className="w-5 h-5 accent-blue-600"
                        />
                        <label htmlFor="remote" className="font-semibold text-gray-700">Remote Only</label>
                    </div>
                </div>
                <button
                    type="submit"
                    className="w-full py-3 text-lg font-semibold bg-gradient-to-r from-blue-600 to-cyan-400 text-white shadow-md rounded hover:from-blue-700 hover:to-cyan-500 transition"
                >
                    Search Jobs
                </button>
            </form>
        </div>
    );
} 