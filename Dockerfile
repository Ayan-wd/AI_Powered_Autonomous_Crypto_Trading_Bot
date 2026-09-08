# ==============================================================================
# Multi-Stage Production Dockerfile for AI Trading Bot (Unified Backend + Frontend)
# Optimized for 100% Free Tier Cloud Deployments (Render.com, Koyeb, Hugging Face)
# ==============================================================================

# --- Stage 1: Build React Dashboard Frontend ---
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Build Python Backend Dependencies ---
FROM python:3.12-slim AS backend-builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --user -r backend/requirements.txt

# --- Stage 3: Final Production Runner ---
FROM python:3.12-slim AS runner
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from backend-builder
COPY --from=backend-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy backend source code, models, and initial data
COPY backend/ ./backend/
COPY models/ ./models/
COPY data/ ./data/

# Copy compiled frontend distribution from frontend-builder
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure data and log directories exist
RUN mkdir -p /app/data /app/logs

# Default port (Render overrides with $PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/api/v1/health/ping || exit 1

# Launch uvicorn server binding to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
