# SocialSeed E2E - Official Docker Image
# Provides a containerized environment for running E2E tests and AI Observability

FROM python:3.11-slim

LABEL maintainer="Dairon Pérez Frías <dairon.perezfrias@gmail.com>"
LABEL description="SocialSeed E2E - Framework for testing REST APIs with AI Observability"
LABEL version="0.1.6"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml setup.py setup.cfg ./
COPY src/ ./src/

# Install dependencies (Explicitly including all dashboard/observability requirements)
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir streamlit uvicorn fastapi httpx python-socketio[asyncio]

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Expose ports: 8501 (Dashboard), 8181 (Observability API)
EXPOSE 8501 8181

# Create non-root user for security
RUN useradd -m -u 1000 e2euser && \
    chown -R e2euser:e2euser /app
USER e2euser

# Set the entrypoint to the e2e CLI dashboard by default
ENTRYPOINT ["e2e"]

# Default command launches the dashboard (which now also starts the observability engine)
CMD ["dashboard", "--host", "0.0.0.0"]
