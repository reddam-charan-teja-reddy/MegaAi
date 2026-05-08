import { useState, useEffect, useRef, useCallback } from 'react';

// Enum for WS status
export const WsStatus = {
  DISCONNECTED: 'Disconnected',
  CONNECTING: 'Connecting',
  CONNECTED: 'Connected',
  ERROR: 'Error',
};

export function useFeederStream(customWsUrl = null) {
  const [stream, setStream] = useState(null);
  const [wsStatus, setWsStatus] = useState(WsStatus.DISCONNECTED);
  const [devices, setDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [targetFps, setTargetFps] = useState(15);
  const [error, setError] = useState(null);
  
  // Telemetry
  const [telemetry, setTelemetry] = useState({ currentFps: 0, bytesPerSec: 0 });

  const wsRef = useRef(null);
  const intervalRef = useRef(null);
  const frameCountRef = useRef(0);
  const bytesRef = useRef(0);
  const fpsIntervalRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Fetch available camera devices on mount
  useEffect(() => {
    async function loadDevices() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true }); // Request permissions first to get labels
        const allDevices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = allDevices.filter(device => device.kind === 'videoinput');
        setDevices(videoDevices);
        if (videoDevices.length > 0) {
          setSelectedDeviceId(videoDevices[0].deviceId);
        }
        // Stop the initial throwaway track used just for permission
        stream.getTracks().forEach(track => track.stop());
      } catch (err) {
        setError('Camera permission denied or no devices found.');
        console.error('Error fetching devices', err);
      }
    }
    loadDevices();
  }, []);

  // Update Telemetry FPS every second
  useEffect(() => {
    fpsIntervalRef.current = setInterval(() => {
      setTelemetry({ 
        currentFps: frameCountRef.current,
        bytesPerSec: bytesRef.current
      });
      frameCountRef.current = 0;
      bytesRef.current = 0;
    }, 1000);

    return () => clearInterval(fpsIntervalRef.current);
  }, []);

  const stopStream = useCallback(() => {
    // Clear capture interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Stop all media tracks
    setStream(prevStream => {
      if (prevStream) {
        prevStream.getTracks().forEach(track => track.stop());
      }
      return null;
    });

    // Close WebSocket gracefully
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setWsStatus(WsStatus.DISCONNECTED);
  }, []); // Removed stream from dependencies to prevent unintended cleanups

  const startStream = useCallback(async (wsUrl, downscaleTarget = { width: 640, height: 480 }) => {
    setError(null);
    if (!selectedDeviceId) {
      setError('No camera selected.');
      return;
    }

    const urlToUse = wsUrl || customWsUrl;
    if (!urlToUse) {
      setError('No WebSocket URL configured.');
      setWsStatus(WsStatus.ERROR);
      return;
    }

    // 1. Initialize WebSocket
    setWsStatus(WsStatus.CONNECTING);
    const ws = new WebSocket(urlToUse);
    ws.binaryType = 'blob'; 
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus(WsStatus.CONNECTED);
    };

    ws.onerror = (e) => {
      console.error('WebSocket Error', e);
      setError('WebSocket connection error.');
      setWsStatus(WsStatus.ERROR);
      stopStream();
    };

    ws.onclose = () => {
      setWsStatus((prev) => prev !== WsStatus.ERROR ? WsStatus.DISCONNECTED : prev);
      stopStream(); // auto-recovery/stop loop if backend drops
    };

    // 2. Initialize Camera
    let activeStream;
    try {
      activeStream = await navigator.mediaDevices.getUserMedia({
        video: { deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined }
      });
      
      // Async Race Condition Check: If user clicked 'Stop' while camera was loading
      if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
         activeStream.getTracks().forEach(track => track.stop());
         return;
      }
      
      setStream(activeStream);
    } catch (err) {
      setError('Failed to start camera. ' + err.message);
      setWsStatus(WsStatus.ERROR);
      if (wsRef.current) wsRef.current.close();
      return;
    }

    // Assign stream to video element in UI
    if (videoRef.current) {
      videoRef.current.srcObject = activeStream;
    }

    // 3. Start Capture Loop
    const canvas = document.createElement('canvas');
    canvasRef.current = canvas;
    canvas.width = downscaleTarget.width;
    canvas.height = downscaleTarget.height;
    const ctx = canvas.getContext('2d');

    const captureIntervalTime = 1000 / targetFps;
    
    intervalRef.current = setInterval(() => {
      // Backpressure Check: Skip frame if WS is not OPEN
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        return;
      }

      if (videoRef.current && videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA) {
        // Draw the downscaled frame to hidden canvas
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        
        // JPEG Compression
        canvas.toBlob((blob) => {
          if (!blob) return;
          
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(blob);
            frameCountRef.current += 1;
            bytesRef.current += blob.size;
          }
        }, 'image/jpeg', 0.8); // 80% quality
      }
    }, captureIntervalTime);

  }, [selectedDeviceId, targetFps, customWsUrl]); // removed stream, wsStatus, stopStream to prevent looping

  // Cleanup on unmount
  useEffect(() => {
    return () => stopStream();
  }, [stopStream]);

  return {
    stream,
    wsStatus,
    devices,
    selectedDeviceId,
    targetFps,
    error,
    telemetry,
    videoRef, // pass to <video> in component
    setSelectedDeviceId,
    setTargetFps,
    startStream,
    stopStream
  };
}
