import asyncio
import time
from typing import List, Dict, Optional
from app.db.database import AsyncSessionLocal
from app.db.models import ROIHistory

class ROIBufferManager:
    """
    Background buffering system that temporarily holds ROI data.
    Flushes rules: 50 records or background tick every few seconds.
    """
    def __init__(self):
        self.buffer: List[Dict] = []
        self.lock = asyncio.Lock()
        self.last_flush_time = time.time()
        self.last_recorded_roi: Dict[str, Dict] = {} # session_id -> {timestamp, x, y}

    async def add_roi(self, session_id: str, roi: tuple):
        """
        Evaluates 1-Second / 5% Shift Rules. Appends to buffer if constraints met.
        """
        if not roi:
            return

        x_min, y_min, x_max, y_max = roi
        current_time = time.time()
        
        last_data = self.last_recorded_roi.get(session_id)
        should_record = False

        if not last_data:
            should_record = True
        else:
            time_diff = current_time - last_data["time"]
            
            # The Flush Logic (1-Second / 5% Rule)
            if time_diff >= 1.0:
                should_record = True
            else:
                # 5% shift means the position changed by 0.05 on the normalized scale
                x_shift = abs(x_min - last_data["x_min"])
                y_shift = abs(y_min - last_data["y_min"])
                if x_shift > 0.05 or y_shift > 0.05:
                    should_record = True

        if should_record:
            self.last_recorded_roi[session_id] = {
                "time": current_time, 
                "x_min": x_min, 
                "y_min": y_min
            }
            
            async with self.lock:
                self.buffer.append({
                    "session_id": session_id,
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max,
                })
                
                # Immediate flush if buffer is hit size 50
                if len(self.buffer) >= 50:
                    asyncio.create_task(self.flush())

    async def flush(self):
        """Bulk INSERT into PostgreSQL and clear buffer"""
        async with self.lock:
            if not self.buffer:
                return
            
            records_to_flush = self.buffer.copy()
            self.buffer.clear()

        try:
            async with AsyncSessionLocal() as db:
                objects = [ROIHistory(**record) for record in records_to_flush]
                db.add_all(objects)
                await db.commit()
                self.last_flush_time = time.time()
                # print(f"Flushed {len(records_to_flush)} records to DB.")
        except Exception as e:
            print(f"Error flushing to DB: {e}")
            # If error occurs, re-add to buffer gracefully
            async with self.lock:
                self.buffer = records_to_flush + self.buffer

    async def start_background_worker(self):
        """Run continuously to ensure buffer is drained when traffic slows."""
        try:
            while True:
                await asyncio.sleep(5)  # flush every 5 seconds if not triggered by limit
                current_time = time.time()
                if current_time - self.last_flush_time >= 5.0:
                    await self.flush()
        except asyncio.CancelledError:
            # flush one last time on shutdown
            await self.flush()

roi_buffer = ROIBufferManager()