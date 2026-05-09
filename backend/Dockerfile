# Stage 1: Build and extract dependencies using 'uv'
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies required by MediaPipe runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies natively
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --frozen --no-dev

# Stage 2: Production execution environment
FROM python:3.12-slim

WORKDIR /app

# Copy system libraries required by mediapipe/numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code safely without cache and test dirs
COPY app /app/app
# We could technically put tests elsewhere, but let's copy only app

# Pre-fetch the Mediapipe TFLite Model at Build-Time (Industry Standard practice for assets, avoids runtime fetching)
RUN wget -O /app/app/cv/face_detection_short_range.tflite "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"

# Make model path explicit for runtime configuration
ENV MODEL_PATH=/app/app/cv/face_detection_short_range.tflite

# Ensure execution works seamlessly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
