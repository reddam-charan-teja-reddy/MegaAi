import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.future import select
from app.core.state import global_state
from app.db.buffer import roi_buffer
from app.db.database import AsyncSessionLocal
from app.db.models import ROIHistory
from app.cv.pipeline import pipeline

router = APIRouter()

@router.websocket("/ws/stream/ingest/{session_id}")
async def ingest_stream(websocket: WebSocket, session_id: str):
    """The Producer (Ingest)"""
    await websocket.accept()
    loop = asyncio.get_running_loop()
    
    # Backpressure Drop Policy marker
    is_processing = False 
    
    try:
        while True:
            data = await websocket.receive_bytes()
            
            # The Drop Policy: If threadpool is busy, ignore incoming frame
            if is_processing:
                continue
                
            is_processing = True
            
            def process_and_update():
                try:
                    # CPU-heavy task via ThreadPool
                    processed_bytes, roi = pipeline.process_frame(data)
                    # Update the Global State memory dictionary thread-safely
                    global_state.update_frame(session_id, processed_bytes, roi)
                    return roi
                except Exception as e:
                    print(f"Pipeline error: {e}")
                    return None

            try:
                # Offload to Thread Pool
                roi = await loop.run_in_executor(None, process_and_update)
                
                # Async write to DB smart buffer
                if roi:
                    await roi_buffer.add_roi(session_id, roi)
            finally:
                is_processing = False

            await websocket.send_json({"status": "received"})
            
    except WebSocketDisconnect:
        global_state.clean_session(session_id)
        # print("Ingest socket disconnected")

@router.websocket("/ws/stream/serve/{session_id}")
async def serve_stream(websocket: WebSocket, session_id: str):
    """The Consumer (Serve). Client reads latest JPEG using polling loop"""
    await websocket.accept()
    try:
        while True:
            # Check for client messages (could be requesting next frame)
            # A common strategy is to wait for the client to say "next", 
            # serving as automatic consumer-side backpressure.
            await websocket.receive_text()
            
            frame_bytes, roi = global_state.get_latest_frame(session_id)
            if not frame_bytes:
                await asyncio.sleep(0.01)
                continue
            
            # Sending Option B: Send the binary frame
            await websocket.send_bytes(frame_bytes)
            
            # (Optional) We could send a trailing text frame with ROI, 
            # however, since the image ALREADY has the Pillow bounding box drawn 
            # onto it per requirements, the client only explicitly needs the JPEG bytes to view it.
            # If explicit JSON data is needed, we would follow up with send_json(roi).
            
    except WebSocketDisconnect:
        # print("Serve socket disconnected")
        pass


@router.get("/api/v1/roi/history/{session_id}")
async def get_roi_history(session_id: str):
    """Standard REST endpoint to get History"""
    async with AsyncSessionLocal() as db:
        stmt = select(ROIHistory).where(ROIHistory.session_id == session_id).order_by(ROIHistory.timestamp.asc())
        result = await db.execute(stmt)
        history = result.scalars().all()
        
        return [
            {
                "timestamp": h.timestamp.isoformat(),
                "x_min": h.x_min,
                "y_min": h.y_min,
                "x_max": h.x_max,
                "y_max": h.y_max
            }
            for h in history
        ]
