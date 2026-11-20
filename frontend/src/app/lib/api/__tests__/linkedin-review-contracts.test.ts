import { expectTypeOf, it } from 'vitest';
import type { components } from '@/generated/api/types';

it('accepts a versioned résumé citation with a locator', () => {
  type Finding = components['schemas']['LinkedInFinding'];
  type ChronologyQuestion = {
    kind: 'consistency_question';
    explanation: string;
    document_locator: string;
    resume_source: components['schemas']['SourceRef'];
    resume_locator: string;
  };

  expectTypeOf<ChronologyQuestion>().toExtend<Finding>();
  expectTypeOf<Omit<ChronologyQuestion, 'resume_locator'>>().not.toExtend<Finding>();
});
