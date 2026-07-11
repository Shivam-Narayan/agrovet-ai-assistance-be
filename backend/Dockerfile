FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user for security
RUN useradd -m -d /app -s /bin/bash appuser

# Set work directory
WORKDIR /app

# Install system dependencies required for OpenCV and MySQLClient
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Ensure all files are owned by the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose port 8000
EXPOSE 8000

# Start server using Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "300"]
