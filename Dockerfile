# Use official Python runtime as base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Copy and install dependencies first (better build caching)
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Change working directory to the Django project folder
WORKDIR /app/backend

# Expose port for Gunicorn
EXPOSE 8009

# Run Gunicorn (optimized settings)
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
