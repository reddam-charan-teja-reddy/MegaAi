# Mega AI

Real-time face detection video streaming system using FastAPI, MediaPipe, PostgreSQL, and a Vite React frontend.

## Quick Start (Docker)

1. Build and start containers:

```bash
docker compose build
docker compose up -d
```

2. Open the UI:

- http://localhost:3000

3. Backend API:

- REST: http://localhost:8000/api/v1/roi/history/{session_id}
- WebSocket ingest: ws://localhost:8000/ws/stream/ingest/{session_id}
- WebSocket serve: ws://localhost:8000/ws/stream/serve/{session_id}

## Configuration

- `MODEL_PATH`: Path to the MediaPipe model file. Default is `face_detection_short_range.tflite`.
  In Docker, the model is baked into the image at `/app/app/cv/face_detection_short_range.tflite`.

## Local Development

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If the model file is missing locally, download it to `backend/app/cv/`:

```bash
curl -L -o backend/app/cv/face_detection_short_range.tflite \
	https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite
```

### Frontend

```bash
cd frontend
bun install
bun run dev
```

## Tests

```bash
cd backend
uv run pytest
```

## Build & Deploy (Overview)

- Backend image builds with `uv sync --frozen --no-dev`, then downloads the MediaPipe model at build time.
- Frontend image builds with `bun` and is served by Nginx.
- `docker compose up -d` starts PostgreSQL, the API, and the UI together on a shared network.
