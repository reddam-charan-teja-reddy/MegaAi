from datetime import datetime
import pytest
from unittest.mock import patch, AsyncMock
from app.db.buffer import ROIBufferManager
from app.core.config import settings

@pytest.mark.asyncio
async def test_roi_buffer_time_threshold():
    """Unit Test: Ensure buffer records ROI if exactly 1 second elapses"""
    buffer = ROIBufferManager()
    
    # Mock flush to do nothing and avoid DB errors
    buffer.flush = AsyncMock()

    # Base ROI coordinates
    roi = (0.1, 0.1, 0.2, 0.2)
    
    with patch("time.time", side_effect=[100.0, 100.5, 101.1]):
        # Call 1 (Time 100.0): Always records the first frame
        await buffer.add_roi("session1", roi)
        assert len(buffer.buffer) == 1

        # Call 2 (Time 100.5): Fails time threshold (0.5s < 1.0s), no coordinate shift
        await buffer.add_roi("session1", roi)
        assert len(buffer.buffer) == 1

        # Call 3 (Time 101.1): Passes time threshold (1.1s > 1.0s)
        await buffer.add_roi("session1", roi)
        assert len(buffer.buffer) == 2

@pytest.mark.asyncio
async def test_roi_buffer_shift_threshold():
    """Unit Test: Ensure buffer records instantly if ROI shifts by > 5%"""
    buffer = ROIBufferManager()
    buffer.flush = AsyncMock()

    roi_start = (0.1, 0.1, 0.2, 0.2)
    roi_shift = (0.16, 0.1, 0.26, 0.2) # X shifted by 0.06 (> 0.05 threshold)
    roi_small_shift = (0.17, 0.1, 0.27, 0.2) # Shifted by 0.01 from previous

    with patch("time.time", side_effect=[100.0, 100.1, 100.2]):
        # Call 1 (Time 100.0): Baseline
        await buffer.add_roi("session2", roi_start)
        
        # Call 2 (Time 100.1): Rapid shift (> 5%), overrides time rule
        await buffer.add_roi("session2", roi_shift)
        assert len(buffer.buffer) == 2

        # Call 3 (Time 100.2): Small shift (< 5%), correctly drops the frame
        await buffer.add_roi("session2", roi_small_shift)
        assert len(buffer.buffer) == 2


@pytest.mark.asyncio
async def test_roi_buffer_shift_threshold_by_size_change():
    buffer = ROIBufferManager()
    buffer.flush = AsyncMock()

    roi_start = (0.1, 0.1, 0.2, 0.2)
    roi_size_change = (0.1, 0.1, 0.26, 0.26)

    with patch("time.time", side_effect=[100.0, 100.1]):
        await buffer.add_roi("session2b", roi_start)
        await buffer.add_roi("session2b", roi_size_change)
        assert len(buffer.buffer) == 2


@pytest.mark.asyncio
async def test_roi_buffer_ignores_none_roi():
    buffer = ROIBufferManager()
    buffer.flush = AsyncMock()

    await buffer.add_roi("session3", None)
    assert len(buffer.buffer) == 0


@pytest.mark.asyncio
async def test_roi_buffer_flush_on_max_size(monkeypatch):
    buffer = ROIBufferManager()
    buffer.flush = AsyncMock()

    monkeypatch.setattr(settings, "BUFFER_MAX_SIZE", 1)

    with patch("app.db.buffer.asyncio.create_task") as mock_task:
        await buffer.add_roi("session4", (0.1, 0.1, 0.2, 0.2))
        assert mock_task.called


@pytest.mark.asyncio
async def test_roi_buffer_flush_requeues_on_error():
    buffer = ROIBufferManager()
    buffer.buffer.append({
        "session_id": "session5",
        "x_min": 0.1,
        "y_min": 0.1,
        "x_max": 0.2,
        "y_max": 0.2,
        "timestamp": datetime.fromtimestamp(100.0),
    })

    class FailingSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def add_all(self, _):
            pass

        async def commit(self):
            raise RuntimeError("DB failure")

    with patch("app.db.buffer.AsyncSessionLocal", return_value=FailingSession()):
        await buffer.flush()
        assert len(buffer.buffer) == 1
