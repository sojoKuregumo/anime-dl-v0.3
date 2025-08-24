# Use a slim Python image to keep size small but allow apt installs
FROM python:3.12-slim

# Use noninteractive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (aria2 for fast downloads, ffmpeg for media probing)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       aria2 \
       ffmpeg \
       ca-certificates \
       curl \
       gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Cleanup old session files that might cause issues
RUN rm -f *.session *.session-journal || true

# Create downloads directory with proper permissions
RUN mkdir -p downloads && chmod 755 downloads

# Expose port used by Koyeb (required for web services)
EXPOSE 8080

# Default command - run the web server to keep the service alive on Koyeb
CMD ["bash", "web.sh"]
