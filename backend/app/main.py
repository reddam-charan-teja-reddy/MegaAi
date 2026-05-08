import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.db.database import init_db
from app.db.buffer import roi_buffer
from app.api.endpoints import router
from app.cv.pipeline import pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup background operations: Database initialization + ML Loading + Background flush worker
    await init_db()
    
    try:
        # Load ML assets into memory at boot time, NOT import time.
        pipeline.setup()
    except FileNotFoundError:
        print("CRITICAL: face_detection_short_range.tflite is missing. Ensure the Dockerfile downloaded the asset.")
        # We don't crash here explicitly so tests can run cleanly without the model
        pass

    worker_task = asyncio.create_task(roi_buffer.start_background_worker())
    
    yield
    
    # Graceful Shutdown phase
    print("Initiating graceful shutdown...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    print("Shutdown complete. All ROIs flushed.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Restrict in production via env
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.WS_HOST, port=settings.WS_PORT, reload=True)