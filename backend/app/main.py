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
    
    # Load ML assets into memory at boot time.
    # In a standard containerized setup, if the model is missing, the application
    # should explicitly Fail Fast at boot, as the Docker image is considered broken.
    pipeline.setup()

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

cors_origins = ["*"]
if settings.CORS_ALLOW_ORIGINS != "*":
    cors_origins = [origin.strip() for origin in settings.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]

# Restrict in production via env
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.WS_HOST, port=settings.WS_PORT, reload=True)