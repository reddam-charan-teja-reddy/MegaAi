import threading
import time
from typing import Dict, Optional, Tuple

class GlobalState:
    """
    Thread-safe Singleton dictionary to hold the most recently processed frame and ROI 
    for an active session_id. Resolves the Producer-Consumer decoupling.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalState, cls).__new__(cls)
                cls._instance.sessions = {}
                cls._instance.session_locks = {}
        return cls._instance

    def _get_lock(self, session_id: str):
        if session_id not in self.session_locks:
            self.session_locks[session_id] = threading.Lock()
        return self.session_locks[session_id]

    def update_frame(self, session_id: str, frame_bytes: bytes, roi_coords: Optional[Tuple[float, float, float, float]] = None):
        """Update the latest frame and ROI for a session safely."""
        with self._get_lock(session_id):
            if session_id not in self.sessions:
                self.sessions[session_id] = {}
                
            self.sessions[session_id]["frame"] = frame_bytes
            self.sessions[session_id]["roi"] = roi_coords
            self.sessions[session_id]["last_updated"] = time.time()

    def get_latest_frame(self, session_id: str):
        """Retrieve the latest frame and ROI."""
        bounds = self.sessions.get(session_id, None)
        if not bounds:
            return None, None
            
        with self._get_lock(session_id):
            return bounds.get("frame"), bounds.get("roi")

    def clean_session(self, session_id: str):
        """Clean up state if required."""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.session_locks:
                del self.session_locks[session_id]

global_state = GlobalState()