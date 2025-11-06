# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create directory for media files
RUN mkdir -p /app/media /app/staticfiles

# Collect static files (with fallback if it fails)
RUN python manage.py collectstatic --noinput --clear

# Expose port 8000
EXPOSE 8000

# Run gunicorn with optimized settings for large file processing
CMD gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
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