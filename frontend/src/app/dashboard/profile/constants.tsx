import { ProfileData } from './types';

export const INITIAL_PROFILE_DATA: ProfileData = {
    user: {
        name: '',
        email: '',
        location: '',
        title: ''
    },
    stats: {
        applications: 0,
        experiences: 0
    },
    resumes: [],
    preferences: {
        roles: [],
        locations: [],
        salaryRange: ''
    },
};
