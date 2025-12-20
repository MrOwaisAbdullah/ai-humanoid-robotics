# Use Python 3.11 slim image optimized for HF Spaces
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pyproject.toml file first
COPY pyproject.toml ./

# Install build dependencies
RUN pip install --no-cache-dir build

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy the rest of the application code
COPY . .

# Create necessary directories
RUN mkdir -p database logs

# Create a non-root user for security (optional for HF Spaces)
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# Expose the port (HF Spaces default)
EXPOSE 7860

# Health check for HF Spaces monitoring
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application with database initialization
CMD ["python", "start_server.py"]