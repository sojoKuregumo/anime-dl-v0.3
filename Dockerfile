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
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Cleanup old session files that might cause issues
RUN rm -f *.session *.session-journal || true

# Expose port used by keep-alive webserver (if applicable)
EXPOSE 8080

# Default command used by Koyeb as web service (keeps service alive)
# If you want to run the bot as a worker, uncomment the alternate CMD.
CMD ["bash", "web.sh"]
# CMD ["bash", "start.sh"]
