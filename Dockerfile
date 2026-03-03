# =============================================================================
# All-in-one Dockerfile: Frontend (build) + Backend (Python/Playwright) + nginx
# =============================================================================

# --- Stage 1: Build the React frontend ---
FROM node:22-alpine AS frontend-build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# --- Stage 2: Runtime — Python + Playwright + nginx ---
FROM python:3.12-slim

WORKDIR /app

# Install nginx and Playwright system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libasound2 libxshmfence1 libx11-xcb1 libxcb1 \
    libxext6 libxfixes3 libexpat1 libglib2.0-0 \
    fonts-liberation libfontconfig1 libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies + Playwright Chromium
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium \
    && python -m playwright install-deps chromium

# Copy backend application code
COPY backend/app/ ./app/

# Copy built frontend assets from Stage 1
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# Copy nginx config for the unified container
COPY nginx.unified.conf /etc/nginx/conf.d/default.conf
# Remove the default nginx site config that conflicts on port 80
RUN rm -f /etc/nginx/sites-enabled/default

# Create tmp directory for runtime output
RUN mkdir -p /app/tmp

# Copy startup entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# nginx on 80 (externally exposed), uvicorn on 8000 (internal only)
EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
