import { describe, expect, it } from 'vitest';

import { extractZodErrors } from '@/lib/form-utils';
import {
  validateCompleteProfile,
  validateEducation,
  validatePersonalInfo,
  validateSkills,
} from './profile-schemas';

const personal = {
  full_name: 'Synthetic Candidate',
  email: 'candidate@example.com',
  location: 'New York',
};

describe('profile validation compatibility', () => {
  it('accepts an omitted optional phone without adding a value', () => {
    const result = validatePersonalInfo(personal);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data).toEqual(personal);
  });

  it('keeps invalid field errors usable by the form', () => {
    const result = validatePersonalInfo({ ...personal, email: 'invalid-email' });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(extractZodErrors(result.error)).toContainEqual({
        field: 'email', message: 'Please enter a valid email address',
      });
    }
  });

  it('rejects oversized skill lists at the named field', () => {
    const result = validateSkills({
      programming_languages: Array.from({ length: 21 }, (_, i) => `Language ${i}`),
      frameworks_libraries: [], tools_platforms: [],
    });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.error.issues[0].path).toEqual(['programming_languages']);
  });

  it('formats every Zod path key without throwing', () => {
    expect(extractZodErrors({ issues: [{
      path: ['experience', 0, Symbol('field')], message: 'Invalid field',
    }] })).toEqual([{ field: 'experience.0.Symbol(field)', message: 'Invalid field' }]);
  });

  it('retains cross-field salary validation on the complete profile', () => {
    const result = validateCompleteProfile({
      ...personal, years_of_experience: 0, career_level: 'early_career',
      professional_summary: 'Built a synthetic example application.',
      programming_languages: ['Python'], frameworks_libraries: [], tools_platforms: [],
      desired_roles: ['Engineer'], preferred_locations: ['New York'],
      salary_range_min: 100, salary_range_max: 50,
    });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.error.issues[0].path).toEqual(['salary_range_max']);
  });

  it('converts supplied dates while leaving optional dates absent', () => {
    const result = validateEducation({
      institution_name: 'Synthetic University', degree_type: 'BS',
      field_of_study: 'Computing', start_date: '2020-01-01',
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.start_date).toEqual(new Date('2020-01-01'));
      expect(result.data).not.toHaveProperty('end_date');
    }
  });
});
