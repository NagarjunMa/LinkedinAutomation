# Architecture Decisions

## OpenAI Integration Architecture

### Decision: Migrate to AsyncOpenAI Client
**Context**: Original code used deprecated `openai.ChatCompletion` API that doesn't work with openai>=1.0.0

**Decision**:
- Use `AsyncOpenAI` client throughout the application
- Implement proper async/await patterns
- Add comprehensive error handling and retry logic

**Rationale**:
- Future-proof compatibility with OpenAI SDK updates
- Better error handling and logging capabilities
- Proper async support for FastAPI endpoints
- Cost tracking and token usage monitoring

**Implementation**:
```python
from openai import AsyncOpenAI

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_response(self, messages: List[Dict]) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
```

## Frontend Validation Architecture

### Decision: Zod + React Hook Form Integration
**Context**: Need comprehensive validation for complex multi-step forms

**Decision**:
- Use Zod for schema validation with TypeScript integration
- Implement custom validation hooks
- Real-time and on-blur validation strategies

**Rationale**:
- Type safety across frontend and backend boundaries
- Runtime validation with compile-time type checking
- Reusable validation schemas

## ADR-001: Consolidate Multi-Agent Resume Evaluation System

### Status: Implemented (January 2024)

### Context
The original resume evaluation system used 12 specialized AI agents running in parallel:
- Each agent made a separate OpenAI API call
- Complex asyncio coordination with individual timeouts
- High cost ($0.15 per evaluation)
- Slow processing (45 seconds average)
- Difficult to maintain and debug

### Decision
Replace the 12-agent system with a single comprehensive AI prompt that combines all evaluation expertise.

### Consequences

**Positive:**
- 75% performance improvement (6s vs 45s)
- 85% cost reduction ($0.02 vs $0.15)
- Simpler error handling (1 point of failure vs 12)
- Easier to maintain and debug
- Consistent evaluation format

**Negative:**
- Less granular analysis per dimension
- Harder to debug specific evaluation aspects
- Single point of failure for entire evaluation

**Mitigations:**
- Comprehensive prompt includes all agent expertise
- Structured JSON response maintains granularity
- Feature flag allows rollback to multi-agent system

## ADR-002: Simplify Referral System to Paste-and-Parse

### Status: Implemented (January 2024)

### Context
Complex database-driven referral management system:
- Multiple database tables for contacts, drafts, sent emails
- State management complexity
- Low user adoption
- Maintenance overhead

### Decision
Replace with stateless paste-and-parse LinkedIn profile functionality.

### Consequences

**Positive:**
- More intuitive user experience
- No database management needed
- Instant contact extraction
- Simpler implementation
- Better performance

**Negative:**
- No persistence of referral history
- Cannot track sent referrals
- No analytics on referral success

**Accepted Trade-offs:**
- Simplicity over feature completeness
- User experience over data collection

## ADR-003: Remove Low-Adoption Complex Features

### Status: Implemented (January 2024)

### Context
Several complex features had low user adoption but high maintenance cost:
- Email tracking with Gmail OAuth
- Browser automation with Playwright
- Complex education management
- Activity calendar
- Time tracking

### Decision
Archive these features and simplify or remove functionality.

### Consequences

**Positive:**
- 40% reduction in codebase complexity
- 25% fewer dependencies
- Faster build and deployment
- Lower maintenance burden
- Better focus on core features

**Negative:**
- Some users may miss removed features
- Reduced functionality scope
- Potential feature requests for removed items

**Mitigation:**
- All code archived for potential restoration
- Core functionality preserved in simpler form
- Clear communication about feature sunset

## ADR-004: Frontend Performance Optimization Strategy

### Status: Planned (January 2024)

### Context
Frontend performance analysis revealed critical issues:
- 1,553-line monolithic API module
- 30-second dashboard auto-refresh
- Synchronous middleware operations
- Missing React optimizations
- Memory leaks

### Decision
Implement phased performance optimization:
1. Split API module into feature chunks
2. Remove auto-refresh, add manual refresh
3. Add session caching
4. Implement React.memo and virtualization
5. Add code splitting and lazy loading

### Expected Outcomes

**Performance Targets:**
- 50% reduction in initial load time
- 60% faster navigation
- 35% smaller bundle size
- 27% lower memory usage

**Implementation Strategy:**
- Phase 1: Critical fixes (API split, auto-refresh)
- Phase 2: React optimizations
- Phase 3: Bundle optimization
- Phase 4: Architecture improvements

## ADR-005: AI Model Selection - GPT-4o-mini

### Status: Active

### Context
Need cost-effective AI processing for multiple features.

### Decision
Standardize on GPT-4o-mini for all AI operations.

### Rationale
- 60% cheaper than GPT-4
- Sufficient quality for job matching and content generation
- Fast response times
- Good token efficiency

### Trade-offs
- Slightly lower quality than GPT-4
- Less capable for complex reasoning
- Acceptable for current use cases
- Better user experience with immediate feedback

**Implementation**:
```typescript
// Schema definition
export const personalInfoSchema = z.object({
  full_name: z.string().min(2).max(100),
  email: z.string().email(),
  phone: z.string().optional().refine(phoneValidation),
  location: z.string().min(1).max(255)
})

// Custom hook
export function useFormValidation<T>(schema: z.ZodSchema<T>) {
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateField = useCallback((name: string, value: any) => {
    const fieldSchema = schema.shape[name as keyof typeof schema.shape]
    const result = fieldSchema.safeParse(value)
    // Handle validation result
  }, [schema])
}
```

### Decision: Skills Database with Autocomplete
**Context**: Need comprehensive skills input with suggestions

**Decision**:
- Maintain predefined skills database categorized by type
- Implement tag-based multi-select component
- Allow custom skill additions with validation

**Rationale**:
- Standardized skills improve job matching accuracy
- Better user experience with suggestions
- Prevents typos and inconsistent naming
- Maintains flexibility for custom skills

## Database Schema Architecture

### Decision: Separate Education Tables
**Context**: Need comprehensive educational information for job matching

**Decision**:
- Create separate tables for education records, certifications, courses, projects
- Use JSON columns for flexible skill arrays
- Add AI-calculated relevance scores

**Rationale**:
- Normalized data structure for better querying
- Flexible skill storage without rigid constraints
- AI-powered relevance scoring for job matching
- Scalable for additional educational categories

**Schema Design**:
```sql
-- Education records for formal education
CREATE TABLE education_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    institution_name VARCHAR(255) NOT NULL,
    degree_type VARCHAR(100) NOT NULL,
    field_of_study VARCHAR(255) NOT NULL,
    gpa FLOAT,
    technical_skills_gained JSONB,
    relevance_score FLOAT -- AI-calculated
);

-- Certifications for professional credentials
CREATE TABLE certifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    issuing_organization VARCHAR(255) NOT NULL,
    skills_validated JSONB,
    relevance_score FLOAT
);
```

## Logging Architecture

### Decision: Railway-Optimized Structured Logging
**Context**: Railway deployment needs better logging for debugging

**Decision**:
- Use JSON-structured logging with consistent fields
- Implement Railway-specific formatters
- Add OpenAI operation tracking

**Rationale**:
- Better log aggregation and searching in Railway
- Consistent structure for automated analysis
- Cost tracking for OpenAI usage
- Improved debugging capabilities

**Implementation**:
```python
class RailwayJSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "jobflow-backend",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName
        }

        if hasattr(record, 'openai_operation'):
            log_entry.update({
                "openai_operation": record.openai_operation,
                "model": getattr(record, 'model', None),
                "tokens_used": getattr(record, 'tokens_used', None),
                "cost_estimate": getattr(record, 'cost_estimate', None)
            })

        return json.dumps(log_entry)
```

## Component Architecture

### Decision: Compound Component Pattern for Forms
**Context**: Complex multi-step forms with varying validation requirements

**Decision**:
- Use compound component patterns for form sections
- Implement step-by-step wizard with progress tracking
- Separate concerns between validation, display, and state management

**Rationale**:
- Better code organization and reusability
- Clear separation of concerns
- Easier testing and maintenance
- Consistent user experience patterns

## AI Integration Architecture

### Decision: Service Layer with Cost Tracking
**Context**: Multiple AI operations across different services

**Decision**:
- Centralized AI service with operation logging
- Cost tracking and usage monitoring
- Fallback strategies for API failures

**Rationale**:
- Better cost control and monitoring
- Consistent error handling across services
- Easier to implement rate limiting
- Centralized configuration management