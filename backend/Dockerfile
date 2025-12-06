# Use Python 3.11 slim image optimized for HF Spaces
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pyproject.toml and requirements.txt
COPY pyproject.toml requirements.txt ./

# Install uv for faster dependency installation
RUN pip install uv

# Install Python dependencies using uv for better caching
RUN uv pip install --system -e .

# Copy the application code
COPY . .

# Create a non-root user for security
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# Expose the port (HF Spaces default)
EXPOSE 7860

# Health check for HF Spaces monitoring
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
