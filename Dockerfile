# Multi-stage Dockerfile for Railway deployment
# This will build both frontend and backend in one container

FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Verify files are copied correctly
RUN ls -la src/lib/validation/ || echo "Validation directory not found"
RUN ls -la src/lib/form-utils.ts || echo "form-utils.ts not found"
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/.next ./static/frontend

# Create uploads directory
RUN mkdir -p uploads/resumes

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]