# Use Python 3.11 slim image for Hugging Face Spaces
FROM python:3.11-slim

# Set environment variables for HF Spaces
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/transformers \
    PORT=7860

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create cache directories
RUN mkdir -p /app/.cache/huggingface /app/.cache/transformers /app/logs

# Copy requirements first for better caching
COPY pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -e .

# Copy the rest of the application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p database logs && \
    touch database/auth.db && \
    chmod +x start_server.py && \
    chmod -R 755 /app

# For HF Spaces compatibility, run as root (avoid permission issues)
# USER user

# Expose the port (HF Spaces default)
EXPOSE 7860

# Health check for HF Spaces monitoring
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application with proper error handling
CMD ["python", "start_server.py"]