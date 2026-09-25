FROM python:3.11-slim

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
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

# The PDF layout contract uses this installed, embeddable production font.
RUN fc-match --format '%{family}\n' 'Liberation Sans' | grep -qi '^Liberation Sans$'

# Set working directory
WORKDIR /app

# Copy locked dependency files
COPY requirements.in requirements.lock ./

# Install Python dependencies from the tested production lockfile
RUN pip install --no-cache-dir -r requirements.lock

# Install the browser in a shared, root-owned location readable by the runtime user.
RUN playwright install chromium && chmod -R a+rX /ms-playwright

# Copy application code
COPY . .

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

# Start the application with dynamic port for Railway. The start script checks
# the schema revision but never upgrades it; release migrations run separately.
CMD ["sh", "scripts/start.sh"]
