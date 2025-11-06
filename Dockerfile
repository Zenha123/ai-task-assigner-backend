# backend/Dockerfile
# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app/backend

COPY . /app/

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8009
EXPOSE 8009

# Run gunicorn with optimized settings for large file processing
CMD gunicorn backend.wsgi:application \
    --bind 0.0.0.0:8009 \
    --workers 2 \
    --threads 4 \
    --worker-class gthread \
    --timeout 300 \
    --graceful-timeout 300 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info    