# Use Python 3.11 slim image optimized for HF Spaces
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pyproject.toml, requirements.txt, and README.md
COPY pyproject.toml requirements.txt README.md ./

# Install uv for faster dependency installation
RUN pip install uv

# Create a non-root user for security
RUN useradd -m -u 1000 user && chown -R user:user /app

# Switch to non-root user
USER user

# Install Python dependencies using uv for better caching
# Note: Not using --system to avoid permission issues
RUN uv pip install -e .

# Copy the rest of the application code
COPY --chown=user:user . .

# Expose the port (HF Spaces default)
EXPOSE 7860

# Health check for HF Spaces monitoring
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
