import React from 'react';
import { useFeederStream, WsStatus } from './useFeederStream';
import './Feeder.css';

const WS_BACKEND_URL = import.meta.env.VITE_WS_BACKEND_URL || 'ws://localhost:8000/ws/feed';
const CAMERA_WIDTH = parseInt(import.meta.env.VITE_CAMERA_WIDTH || '640', 10);
const CAMERA_HEIGHT = parseInt(import.meta.env.VITE_CAMERA_HEIGHT || '480', 10);

const Feeder = () => {
  const {
    wsStatus,
    devices,
    selectedDeviceId,
    targetFps,
    error,
    telemetry,
    videoRef,
    setSelectedDeviceId,
    setTargetFps,
    startStream,
    stopStream
  } = useFeederStream();

  const isStreaming = wsStatus === WsStatus.CONNECTED;

  const handleToggleStream = () => {
    if (isStreaming || wsStatus === WsStatus.CONNECTING) {
      stopStream();
    } else {
      startStream(WS_BACKEND_URL, { width: CAMERA_WIDTH, height: CAMERA_HEIGHT });
    }
  };

  const getStatusBadge = () => {
    switch (wsStatus) {
      case WsStatus.CONNECTED:
        return <span className="badge badge-green">🟢 Streaming</span>;
      case WsStatus.CONNECTING:
        return <span className="badge badge-yellow">🟡 Connecting</span>;
      case WsStatus.ERROR:
        return <span className="badge badge-red">🔴 Error</span>;
      default:
        return <span className="badge badge-red">🔴 Offline</span>;
    }
  };

  return (
    <div className="feeder-container">
      <div className="header">
        <h2>Feeder (Ingest Engine)</h2>
        <div className="telemetry-panel">
          {getStatusBadge()}
          <span className="telemetry-item">
            <strong>FPS:</strong> {telemetry.currentFps}
          </span>
          <span className="telemetry-item">
            <strong>Bandwidth:</strong> {(telemetry.bytesPerSec / 1024).toFixed(2)} KB/s
          </span>
        </div>
      </div>

      {error && (
        <div className="error-console">
          <strong>Error: </strong> {error}
        </div>
      )}

      <div className="viewport">
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          muted 
          className="video-preview"
          poster="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100%' height='100%'><rect width='100%' height='100%' fill='%23333'/><text x='50%' y='50%' fill='%23777' text-anchor='middle' alignment-baseline='middle'>Camera Offline</text></svg>"
        ></video>
      </div>

      <div className="control-bar">
        <div className="control-group">
          <label htmlFor="device-select">Camera:</label>
          <select 
            id="device-select"
            value={selectedDeviceId} 
            onChange={(e) => setSelectedDeviceId(e.target.value)}
            disabled={isStreaming}
          >
            {devices.length === 0 && <option>Loading...</option>}
            {devices.map(device => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label || `Camera ${device.deviceId.substring(0, 5)}...`}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="fps-slider">Target FPS ({targetFps}):</label>
          <input 
            id="fps-slider"
            type="range" 
            min="1" 
            max="30" 
            value={targetFps} 
            onChange={(e) => setTargetFps(parseInt(e.target.value, 10))}
            disabled={isStreaming} // Optional: allow changing mid-stream by reloading interval, but disabled is safer for now
          />
        </div>

        <button 
          className={`action-btn ${isStreaming ? 'btn-stop' : 'btn-start'}`}
          onClick={handleToggleStream}
        >
          {isStreaming ? 'Stop Stream' : 'Connect & Stream'}
        </button>
      </div>
    </div>
  );
};

export default Feeder;
