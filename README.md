# Face Detection Streaming System

Real-time face detection video streaming system using FastAPI, MediaPipe, PostgreSQL, and a Vite React frontend.

## Architecture

**Frontend**

- **Feeder**: Captures webcam video, downscales it, JPEG-compresses, and streams frames over WebSocket.
- **Viewer**: Receives processed frames over WebSocket and polls REST for ROI history.

**Backend**

- **Ingest WS**: Receives JPEG bytes, runs face detection in a thread pool, draws ROI, stores ROI in buffer.
- **Serve WS**: Streams latest processed frame from in-memory state.
- **REST**: Returns ROI history from PostgreSQL.

**Data Flow**

1. Feeder sends JPEG bytes to `WS /ws/stream/ingest/{session_id}`.
2. Backend detects face, draws ROI, updates in-memory state, buffers ROI for DB.
3. Viewer receives frames from `WS /ws/stream/serve/{session_id}` and polls `GET /api/v1/roi/history/{session_id}`.

Note: The consumer stream is blank until the Feeder starts streaming with the same `session_id`.

**Architecture Diagram**

- [docs/architecture.svg](docs/architecture.svg)

## API Endpoints

- `WS /ws/stream/ingest/{session_id}`: Ingests JPEG frames
- `WS /ws/stream/serve/{session_id}`: Streams processed JPEG frames
- `GET /api/v1/roi/history/{session_id}`: Returns ROI history as JSON

ROI history is served over REST (correct for queryable history). Live frames are served over WebSocket (low latency).

## Configuration

Backend (`backend/.env` or environment variables):

- `DATABASE_URL`
- `WS_HOST`, `WS_PORT`
- `MODEL_PATH` (default `face_detection_short_range.tflite`)
- `CORS_ALLOW_ORIGINS` (comma-separated or `*`)
- `BUFFER_FLUSH_INTERVAL`, `BUFFER_MAX_SIZE`, `ROI_SHIFT_THRESHOLD`, `ROI_TIME_THRESHOLD`
- `MAX_FRAME_BYTES` (frame size limit for ingest WS)

Frontend (`frontend/.env` or environment variables):

- `VITE_API_BASE_URL` (ex: `http://localhost:8000`)
- `VITE_WS_BACKEND_URL` (ex: `ws://localhost:8000`)
- `VITE_CAMERA_WIDTH`, `VITE_CAMERA_HEIGHT`

## Quick Start (Docker)

```bash
docker compose build
docker compose up -d
```

Open the UI:

- http://localhost:3000

If the backend fails to start with `libGLESv2.so.2` missing, rebuild the backend image:

```bash
docker compose build backend --no-cache
docker compose up -d
```

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

Backend:

```bash
cd backend
uv run pytest
```

Frontend:

```bash
cd frontend
bun run test
```

## Submission Notes

- The architecture diagram is provided in [docs/architecture.svg](docs/architecture.svg).
- The MediaPipe model is baked into the backend container at build time.

## Build & Deploy (Overview)

- Backend image builds with `uv sync --frozen --no-dev`, then downloads the MediaPipe model at build time.
- Frontend image builds with `bun` and is served by Nginx.
- `docker compose up -d` starts PostgreSQL, the API, and the UI together on a shared network.

## Troubleshooting

- **Consumer stream is empty**: Ensure the Feeder is running and sending frames with the same `session_id`.
- **REST ROI shows errors**: Ensure backend is running at `http://localhost:8000`.

## AI Usage Disclosure

GitHub Copilot (GPT-5.2-Codex) was used to assist with code scaffolding, test outlines, and documentation drafts.
All generated code was reviewed and edited to match requirements and standards.
