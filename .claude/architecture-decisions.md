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