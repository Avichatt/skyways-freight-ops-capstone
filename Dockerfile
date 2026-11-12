# Multi-purpose, production-ready container for SkyWays Autonomous Dock Scheduling
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install minimal OS dependencies for healthchecks and builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project code, models, data, and tests
COPY data/ ./data/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY src/ ./src/
COPY tests/ ./tests/

# Expose FastAPI prediction service port
EXPOSE 8000

# Default command: execute the automated regression test suite
CMD ["pytest", "tests/", "-v"]

