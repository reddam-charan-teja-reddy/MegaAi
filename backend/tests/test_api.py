from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.core.state import global_state
from app.core.config import settings
from starlette.websockets import WebSocketDisconnect
import pytest


def test_websocket_ingest_updates_state_and_buffer(client):
    session_id = "test_session"
    processed_bytes = b"processed_jpeg_bytes"
    roi = (0.1, 0.1, 0.9, 0.9)

    with patch("app.api.endpoints.pipeline.process_frame", return_value=(processed_bytes, roi)) as mock_process, \
         patch("app.api.endpoints.roi_buffer.add_roi", new_callable=AsyncMock) as mock_add_roi:
        with client.websocket_connect(f"/ws/stream/ingest/{session_id}") as websocket:
            websocket.send_bytes(b"raw_jpeg_bytes")
            data = websocket.receive_json()
            assert data["status"] == "received"

        frame, saved_roi = global_state.get_latest_frame(session_id)
        assert frame == processed_bytes
        assert saved_roi == roi
        mock_process.assert_called_once()
        mock_add_roi.assert_awaited_once_with(session_id, roi)

    global_state.clean_session(session_id)


def test_websocket_serve_returns_latest_frame(client):
    session_id = "serve_session"
    frame_bytes = b"frame_bytes"

    global_state.update_frame(session_id, frame_bytes, None)

    with client.websocket_connect(f"/ws/stream/serve/{session_id}") as websocket:
        websocket.send_text("next")
        received = websocket.receive_bytes()
        assert received == frame_bytes

    global_state.clean_session(session_id)


def test_rest_history_endpoint_returns_rows(client):
    fake_row = SimpleNamespace(
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        x_min=0.1,
        y_min=0.2,
        x_max=0.3,
        y_max=0.4,
    )

    with patch("app.api.endpoints.AsyncSessionLocal") as mock_db:
        mock_db.return_value.__aenter__.return_value.execute = AsyncMock(
            return_value=AsyncMock(
                scalars=lambda: AsyncMock(all=lambda: [fake_row])
            )
        )

        response = client.get("/api/v1/roi/history/demo_session")
        assert response.status_code == 200
        assert response.json() == [
            {
                "timestamp": "2025-01-01T00:00:00+00:00",
                "x_min": 0.1,
                "y_min": 0.2,
                "x_max": 0.3,
                "y_max": 0.4,
            }
        ]


def test_websocket_ingest_rejects_large_frame(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_FRAME_BYTES", 10)

    with client.websocket_connect("/ws/stream/ingest/oversize") as websocket:
        websocket.send_bytes(b"x" * 20)
        with pytest.raises(WebSocketDisconnect):
            websocket.receive()
