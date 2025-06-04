

# ==================================
# Stage 1: Build Dependencies
# ==================================
FROM python:3.11-slim as builder
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /opt/venv
# Install venv and create virtual environment
RUN python -m venv .
ENV PATH="/opt/venv/bin:$PATH"
# Copy only requirements to leverage cache
COPY requirements.txt .
# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# ==================================
# Stage 2: Final Image
# ==================================
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PORT=8000
WORKDIR $APP_HOME

# Install runtime dependencies for libmagic
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/*
# Create non-root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser
# Copy venv from builder
COPY --from=builder /opt/venv $APP_HOME/venv
# Copy app code
COPY --chown=appuser:appgroup . $APP_HOME
# Activate venv
ENV PATH="$APP_HOME/venv/bin:$PATH"
# Expose the port
EXPOSE $PORT
# Switch to non-root user
USER appuser
# Run the FastAPI app using Uvicorn
CMD ["python", "main.py"]
