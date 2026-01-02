# Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY main.py ./
COPY calculations ./calculations
COPY data ./data
COPY integrations ./integrations
COPY models ./models
COPY routers ./routers

# Install python dependencies
RUN uv pip install --system -r pyproject.toml

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
