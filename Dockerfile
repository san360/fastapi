# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose the port
EXPOSE 3978

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3978/health || exit 1

# Default command - can be overridden
CMD ["python", "main.py"]
