import { useState, useEffect, useRef } from 'react';

export default function Viewer({ sessionId }) {
  const [history, setHistory] = useState([]);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const defaultHttpBase = import.meta.env.VITE_API_BASE_URL
    || `${window.location.protocol}//${window.location.hostname}:8000`;
  const defaultWsBase = import.meta.env.VITE_WS_BACKEND_URL
    || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.hostname}:8000`;
  
  // 1. Fetch historical ROI data from REST API
  const fetchROIHistory = async (signal) => {
    try {
      const response = await fetch(`${defaultHttpBase}/api/v1/roi/history/${sessionId}`, { signal });
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        console.error('Failed to fetch ROI history', e);
      }
    }
  };

  useEffect(() => {
    // Poll the REST API for ROI history every 2 seconds
    const controller = new AbortController();
    fetchROIHistory(controller.signal);
    const interval = setInterval(() => fetchROIHistory(controller.signal), 2000);
    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [sessionId, defaultHttpBase]);

  // 2. Consume real-time video stream over WebSockets
  useEffect(() => {
    const ws = new WebSocket(`${defaultWsBase}/ws/stream/serve/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      // Initiate request cycle for first frame
      ws.send("next");
    };

    ws.onmessage = async (event) => {
      // The backend serves jpeg bytes natively. Draw them into the canvas.
      const blob = event.data;
      if (blob instanceof Blob) {
        const bitmap = await createImageBitmap(blob);
        const canvas = canvasRef.current;
        if (canvas) {
          const ctx = canvas.getContext('2d');
          
          // Set canvas dimensions strictly the first time to avoid stuttering bounds
          if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
            canvas.width = bitmap.width;
            canvas.height = bitmap.height;
          }
          
          ctx.drawImage(bitmap, 0, 0);
        }
        bitmap.close();
      }
      
      // Request next frame instantly (Consumer-side backpressure)
      if (ws.readyState === WebSocket.OPEN) {
        requestAnimationFrame(() => ws.send("next"));
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [sessionId, defaultWsBase]);

  return (
    <div style={{ display: 'flex', gap: '2rem' }}>
      <div className="viewer-video">
        <h2>Consumer Stream</h2>
        <canvas 
          ref={canvasRef} 
          style={{ width: '480px', height: '360px', backgroundColor: '#111' }} 
        />
      </div>
      
      <div className="viewer-roi-data">
        <h2>ROI History (REST API)</h2>
        <div style={{ maxHeight: '360px', overflowY: 'auto', border: '1px solid #ccc', padding: '1rem', width: '300px' }}>
          {history.length === 0 ? (
            <p>No bounding boxes recorded yet.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {history.map((record, idx) => (
                <li key={idx} style={{ marginBottom: '10px', fontSize: '12px' }}>
                  <strong>{new Date(record.timestamp).toLocaleTimeString()}:</strong><br/>
                  ({record.x_min.toFixed(2)}, {record.y_min.toFixed(2)}) to ({record.x_max.toFixed(2)}, {record.y_max.toFixed(2)})
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
