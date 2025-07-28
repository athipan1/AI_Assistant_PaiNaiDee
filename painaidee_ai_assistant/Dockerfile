# PaiNaiDee AI Assistant Dockerfile
# Multi-stage build for production optimization

# Base image with Python and CUDA support (optional)
FROM nvidia/cuda:11.8-runtime-ubuntu22.04 as gpu-base
# Use this base for GPU support

FROM python:3.10-slim as cpu-base
# Use this base for CPU-only deployment

# Choose the appropriate base image
# For GPU deployment: FROM gpu-base as base
# For CPU deployment: FROM cpu-base as base
FROM cpu-base as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create models directory for HuggingFace cache
RUN mkdir -p /app/models
ENV TRANSFORMERS_CACHE=/app/models

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]

# Alternative production command with gunicorn (uncomment if preferred)
# CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]