# TUI Resume - Docker Image
# Python 3.11 slim base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY logs/ ./logs/

# Create non-root user for security
RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    chown -R appuser:appgroup /app

# Generate SSH host key (or mount as volume for persistence)
RUN ssh-keygen -f /app/host_key -N "" -t rsa && \
    chown appuser:appgroup /app/host_key /app/host_key.pub

# Switch to non-root user
USER appuser

# Expose SSH port (container internal port)
EXPOSE 2222

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color

# Health check - verify SSH server is listening
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 2222)); s.close()"

# Run the SSH server
CMD ["python", "-m", "src.tui_resume.ssh_server"]
