# Multi-stage Dockerfile for Railway deployment
# This will build both frontend and backend in one container

FROM node:22-alpine AS frontend-builder
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
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    fontconfig \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install the browser binary used by Playwright PDF rendering.
RUN playwright install chromium

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

# Start the application. The backend start script applies Alembic migrations
# first so deployed code and database schema stay in sync.
CMD ["sh", "scripts/start.sh"]
