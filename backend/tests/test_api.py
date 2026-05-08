import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.cv.pipeline import FaceDetectionPipeline

client = TestClient(app)

@patch("app.db.buffer.roi_buffer.add_roi", new_callable=AsyncMock)
@patch.object(FaceDetectionPipeline, "process_frame")
def test_websocket_ingest_producer(mock_process, mock_add_roi):
    """
    Blackbox Test: The entire API producer endpoint.
    Mocks the ML pipeline to simulate parsing an image and mocks the async DB add to isolate scope.
    """
    # Configure the mock ML pipeline to return fake parsed bytes and ROI
    mock_process.return_value = (b"processed_jpeg_bytes", (0.1, 0.1, 0.9, 0.9))

    with client.websocket_connect("/ws/stream/ingest/test_session") as websocket:
        # Send raw bytes (Feeder simulation)
        websocket.send_bytes(b"raw_jpeg_bytes")
        websocket.send_bytes(b"raw_jpeg_bytes_2")

        # Expect API acknowledgment back
        data = websocket.receive_json()
        assert data["status"] == "received"
        
        # Verify the dependency was explicitly called correctly
        assert mock_process.called

def test_rest_history_endpoint_empty():
    """
    Blackbox Test: The REST Data API endpoint.
    """
    with patch("app.api.endpoints.AsyncSessionLocal") as mock_db:
        # Setup deep mock for SQLAlchemy AsyncSession execution
        mock_db.return_value.__aenter__.return_value.execute = AsyncMock(return_value=AsyncMock(scalars=lambda: AsyncMock(all=lambda: [])))
        
        response = client.get("/api/v1/roi/history/demo_session")
        assert response.status_code == 200
        assert response.json() == []
