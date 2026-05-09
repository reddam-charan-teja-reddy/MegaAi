## Backend

FastAPI service for ingesting video frames, detecting faces, and serving processed frames and ROI history.

### Run locally

```bash
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Required model

Place the model at `app/cv/face_detection_short_range.tflite` or set `MODEL_PATH` to an absolute path.

```bash
curl -L -o app/cv/face_detection_short_range.tflite \
	https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite
```

### Configuration

- `DATABASE_URL`
- `MODEL_PATH`
- `CORS_ALLOW_ORIGINS`
- `BUFFER_FLUSH_INTERVAL`, `BUFFER_MAX_SIZE`, `ROI_SHIFT_THRESHOLD`, `ROI_TIME_THRESHOLD`
- `MAX_FRAME_BYTES`

### Tests

```bash
uv run pytest
```

### Troubleshooting

- If you see `libGLESv2.so.2` missing inside Docker, rebuild:

```bash
docker compose build backend --no-cache
docker compose up -d
```
