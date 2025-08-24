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
       build-essential \
       jq \  # Added for JSON parsing in start scripts
    && rm -rf /var/lib/apt/lists/*

# Create downloads directory with proper permissions
RUN mkdir -p /app/downloads && chmod 755 /app/downloads

# Copy and install Python requirements
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Cleanup old session files that might cause issues
RUN rm -f *.session *.session-journal || true

# Create aria2 configuration directory and file
RUN mkdir -p /etc/aria2
COPY aria2.conf /etc/aria2/aria2.conf

# Expose port used by keep-alive webserver (if applicable)
EXPOSE 8080

# Default command - run the bot directly instead of web.sh
CMD ["bash", "start.sh"]
