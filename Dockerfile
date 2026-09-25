# Multi-stage Dockerfile for Railway deployment
# This will build both frontend and backend in one container

FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Verify files are copied correctly
RUN ls -la src/lib/validation/ || echo "Validation directory not found"
RUN ls -la src/lib/form-utils.ts || echo "form-utils.ts not found"
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONDONTWRITEBYTECODE=1

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

# Install the same locked backend dependencies used by CI and backend/Dockerfile.
COPY backend/requirements.in backend/requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

# Install the browser in a shared, root-owned location readable by the runtime user.
RUN playwright install chromium && chmod -R a+rX /ms-playwright

# Copy backend code
COPY backend/ ./

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/.next ./static/frontend

# Keep application code and browser binaries root-owned. Only runtime data paths
# and the user's cache/home need write permission.
RUN groupadd --gid 10001 prism && \
    useradd --uid 10001 --gid prism --create-home --home-dir /home/prism --shell /usr/sbin/nologin prism && \
    mkdir -p /app/logs /app/uploads/resumes && \
    chown -R prism:prism /app/logs /app/uploads /home/prism

ENV HOME=/home/prism
USER prism:prism

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f -A PrismPro-Container-Health/1.0 http://localhost:8000/health || exit 1

# Start the application. The backend start script checks the schema revision;
# release migrations run separately before this image receives traffic.
CMD ["sh", "scripts/start.sh"]
