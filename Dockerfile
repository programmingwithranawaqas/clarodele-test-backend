# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create directory for temporary files
RUN mkdir -p /tmp/audio_migration

# Expose the Cloud Run port
EXPOSE 8080
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

# Start Uvicorn on 0.0.0.0 and port from environment variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
