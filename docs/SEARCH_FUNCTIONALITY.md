# Job Search Functionality

## Overview

The JobFlow Pro application now includes a comprehensive search functionality that allows users to search through job listings by company name, job title, location, skills, and other criteria. The search is implemented with both frontend and backend components for optimal performance and user experience.

## Features

### 🔍 **Comprehensive Search**
- **Company Name**: Search by exact or partial company names
- **Job Title**: Find jobs by title keywords
- **Location**: Search by city, state, or remote work
- **Skills**: Search through required skills and technologies
- **Description**: Full-text search through job descriptions
- **Requirements**: Search through job requirements

### ⚡ **Real-time Search**
- **Debounced Input**: 300ms delay to prevent excessive API calls
- **Live Suggestions**: Auto-complete suggestions as you type
- **Instant Results**: Fast search results with loading states

### 🎯 **Smart Search Features**
- **Fuzzy Matching**: Finds results even with partial matches
- **Relevance Scoring**: Results ordered by relevance and recency
- **Search History**: Remembers recent searches for quick access
- **Keyboard Shortcuts**: Cmd+F (Mac) or Ctrl+F (Windows) to open search

### 📱 **Responsive Design**
- **Desktop**: Full search bar in header with modal results
- **Mobile**: Search button that opens full-screen modal
- **Touch-friendly**: Optimized for mobile interactions

## Backend API

### Search Endpoint
```
GET /api/v1/search/?q={query}&limit={limit}
```

**Parameters:**
- `q` (required): Search query string
- `limit` (optional): Maximum results to return (default: 20, max: 100)
- `user_id` (optional): User ID for RLS context (default: "demo_user")

**Response:**
```json
[
  {
    "id": 1,
    "title": "Software Engineer",
    "company": "Google",
    "location": "Mountain View, CA",
    "description": "Join our team...",
    "requirements": "Bachelor's degree...",
    "job_type": "Full-time",
    "experience_level": "Mid-level",
    "salary_range": "$120,000 - $180,000",
    "skills": ["Python", "JavaScript", "React"],
    "application_url": "https://careers.google.com/jobs/...",
    "source": "linkedin",
    "source_url": "https://linkedin.com/jobs/...",
    "is_active": true,
    "posted_date": "2024-01-15T10:00:00Z",
    "extracted_date": "2024-01-15T12:00:00Z",
    "applied": false,
    "compatibility_score": 85,
    "ai_insights": "Strong match based on skills..."
  }
]
```

### Suggestions Endpoint
```
GET /api/v1/search/suggestions?q={query}&limit={limit}
```

**Parameters:**
- `q` (required): Partial search query
- `limit` (optional): Maximum suggestions (default: 10, max: 50)

**Response:**
```json
[
  "Software Engineer",
  "Google",
  "Mountain View, CA",
  "Python Developer",
  "Remote"
]
```

### Stats Endpoint
```
GET /api/v1/search/stats
```

**Response:**
```json
{
  "total_jobs": 1250,
  "unique_companies": 340,
  "unique_locations": 85
}
```

## Frontend Components

### 1. SophisticatedHeader
- **Location**: `frontend/src/components/sophisticated-header.tsx`
- **Features**: 
  - Search bar in header (desktop)
  - Search button (mobile)
  - Keyboard shortcut support (Cmd+F)
  - Triggers search modal

### 2. JobSearchModal
- **Location**: `frontend/src/components/job-search-modal.tsx`
- **Features**:
  - Full-screen search interface
  - Real-time suggestions
  - Search history
  - Quick search categories
  - Responsive design

### 3. JobSearchResults
- **Location**: `frontend/src/components/job-search-results.tsx`
- **Features**:
  - Job card display
  - Compatibility scoring
  - Application status
  - Skills display
  - Action buttons

### 4. Search Hooks
- **Location**: `frontend/src/hooks/use-job-search.ts`
- **Features**:
  - `useJobSearch`: Main search functionality
  - `useSearchSuggestions`: Auto-complete suggestions
  - Debounced queries
  - Error handling
  - Caching

## Search Algorithm

### 1. **Query Processing**
- Trim whitespace and normalize input
- Handle special characters and encoding
- Apply debouncing to prevent excessive requests

### 2. **Database Search**
- **OR Logic**: Search across multiple fields simultaneously
- **Case Insensitive**: Uses `ILIKE` for flexible matching
- **JSON Search**: Special handling for skills array
- **Fuzzy Matching**: Partial matches with `%` wildcards

### 3. **Relevance Scoring**
```sql
ORDER BY
  -- Exact company match (highest priority)
  CASE 
    WHEN company ILIKE 'query' THEN 1
    WHEN company ILIKE 'query%' THEN 2
    WHEN company ILIKE '%query%' THEN 3
    ELSE 4
  END,
  -- Exact title match
  CASE 
    WHEN title ILIKE 'query' THEN 1
    WHEN title ILIKE 'query%' THEN 2
    WHEN title ILIKE '%query%' THEN 3
    ELSE 4
  END,
  -- Recency
  extracted_date DESC
```

### 4. **Performance Optimization**
- **Indexes**: Database indexes on searchable fields
- **Pagination**: Limit results to prevent large responses
- **Caching**: React Query for client-side caching
- **Debouncing**: Reduce server load

## Usage Examples

### Basic Search
```typescript
const { searchResults, isLoading } = useJobSearch({
  query: "software engineer",
  limit: 20
})
```

### Company Search
```typescript
const { searchResults } = useJobSearch({
  query: "google",
  limit: 10
})
```

### Skills Search
```typescript
const { searchResults } = useJobSearch({
  query: "python react",
  limit: 15
})
```

### Location Search
```typescript
const { searchResults } = useJobSearch({
  query: "remote",
  limit: 25
})
```

## Configuration

### Environment Variables
```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend
DATABASE_URL=postgresql://user:pass@localhost/db
```

### Database Indexes
```sql
-- Recommended indexes for better search performance
CREATE INDEX idx_job_title_search ON job_listings USING gin(to_tsvector('english', title));
CREATE INDEX idx_job_company_search ON job_listings USING gin(to_tsvector('english', company));
CREATE INDEX idx_job_location_search ON job_listings USING gin(to_tsvector('english', location));
CREATE INDEX idx_job_description_search ON job_listings USING gin(to_tsvector('english', description));
CREATE INDEX idx_job_skills_search ON job_listings USING gin(skills);
```

## Testing

### Backend Testing
```bash
cd backend
python test_search_api.py
```

### Frontend Testing
1. Open the application
2. Click the search bar or press Cmd+F
3. Type a search query
4. Verify results appear
5. Test suggestions and history

### Test Cases
- [ ] Basic text search
- [ ] Company name search
- [ ] Job title search
- [ ] Location search
- [ ] Skills search
- [ ] Empty query handling
- [ ] Special characters
- [ ] Long queries
- [ ] Mobile responsiveness
- [ ] Keyboard shortcuts

## Troubleshooting

### Common Issues

1. **No Results Found**
   - Check if jobs exist in database
   - Verify search query format
   - Check database connection

2. **Slow Search Performance**
   - Add database indexes
   - Reduce result limit
   - Check server resources

3. **Frontend Not Loading**
   - Verify API URL configuration
   - Check network connectivity
   - Review browser console for errors

4. **Suggestions Not Working**
   - Check suggestions endpoint
   - Verify query length (minimum 2 characters)
   - Review network requests

### Debug Mode
Enable debug logging in the backend:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- [ ] **Advanced Filters**: Salary range, job type, experience level
- [ ] **Saved Searches**: Save and manage search queries
- [ ] **Search Analytics**: Track popular searches and trends
- [ ] **AI-Powered Search**: Semantic search using embeddings
- [ ] **Search Export**: Export search results to CSV/PDF
- [ ] **Search Alerts**: Email notifications for new matching jobs
- [ ] **Search History**: Detailed search history with timestamps
- [ ] **Search Suggestions**: ML-powered suggestions based on user behavior

### Performance Improvements
- [ ] **Elasticsearch Integration**: Full-text search engine
- [ ] **Search Caching**: Redis-based result caching
- [ ] **Search Analytics**: Query performance monitoring
- [ ] **Auto-complete**: Trie-based suggestion system
- [ ] **Search Indexing**: Background job indexing

## Support

For issues or questions about the search functionality:

1. Check this documentation
2. Review the test cases
3. Check the browser console for errors
4. Verify API endpoints are working
5. Contact the development team

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Maintainer**: JobFlow Pro Development Team
