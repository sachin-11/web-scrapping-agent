# Use the official Microsoft Playwright Python base image
# This contains all system-level dependencies for Chromium, Firefox and WebKit
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Copy requirements file first to optimize docker caching layer
COPY requirements.txt /app/

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure playwright browser binaries match requirements
RUN playwright install chromium

# Copy backend source code to container
COPY . /app/

# Create folders for output results and images
RUN mkdir -p /app/outputs/images

# Expose port
EXPOSE 8000

# Launch uvicorn, reading Render's dynamic PORT environment variable if present
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
