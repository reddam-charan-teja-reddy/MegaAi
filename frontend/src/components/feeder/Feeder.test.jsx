import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Feeder from './Feeder';

// Mock matchMedia and getUserMedia and enumerateDevices
Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn(),
    enumerateDevices: vi.fn(),
  },
});

describe('Feeder Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mocks
    navigator.mediaDevices.getUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    });

    navigator.mediaDevices.enumerateDevices.mockResolvedValue([
      { deviceId: 'camera-1', kind: 'videoinput', label: 'Front Camera' },
      { deviceId: 'camera-2', kind: 'videoinput', label: 'Back Camera' },
    ]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the Feeder UI elements', async () => {
    render(<Feeder />);
    
    // Check Title
    expect(screen.getByText('Feeder (Ingest Engine)')).toBeInTheDocument();
    
    // Check initial offline status
    expect(screen.getByText('🔴 Offline')).toBeInTheDocument();
    
    // Check Connect button
    expect(screen.getByRole('button', { name: /Connect & Stream/i })).toBeInTheDocument();
    
    // Check devices load asynchronously
    await waitFor(() => {
      expect(screen.getByText(/Front Camera/i)).toBeInTheDocument();
      expect(screen.getByText(/Back Camera/i)).toBeInTheDocument();
    });
  });

  it('changes target FPS using slider', async () => {
    render(<Feeder />);
    
    // Wait for the async device fetching to finish before interacting, 
    // this prevents the React act(...) warnings about background state updates.
    await waitFor(() => expect(screen.getByText(/Front Camera/i)).toBeInTheDocument());

    // Check initial FPS slider (default is 15 in the hook setup)
    const slider = screen.getByLabelText(/Target FPS/i);
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveValue('15');
    
    // Change via slider
    fireEvent.change(slider, { target: { value: '24' } });
    expect(slider).toHaveValue('24');
    expect(screen.getByText(/Target FPS \(24\):/i)).toBeInTheDocument();
  });

  it('shows error UI if getUserMedia fails', async () => {
    // Suppress console.error solely for this test so the terminal stays clean
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    navigator.mediaDevices.getUserMedia.mockRejectedValue(new Error('Permission denied'));
    
    render(<Feeder />);
    
    await waitFor(() => {
      expect(screen.getByText(/Camera permission denied/i)).toBeInTheDocument();
    });
    
    consoleSpy.mockRestore();
  });

  it('starts streaming and establishes WebSocket connection when clicked', async () => {
    // 1. Mock the browser's WebSocket API
    const mockSend = vi.fn();
    const mockClose = vi.fn();
    global.WebSocket = vi.fn().mockImplementation(function () {
      this.send = mockSend;
      this.close = mockClose;
      this.readyState = 1; // WebSocket.OPEN
      // Simulate successful connection right away
      setTimeout(() => this.onopen && this.onopen(), 0); 
    });

    render(<Feeder />);
    await waitFor(() => expect(screen.getByText(/Front Camera/i)).toBeInTheDocument());

    // 2. Click Connect
    const button = screen.getByRole('button', { name: /Connect & Stream/i });
    fireEvent.click(button);

    // 3. Verify WebSocket was instantiated with our env variable or fallback
    expect(global.WebSocket).toHaveBeenCalled();

    // 4. Verify UI updates to Streaming state
    await waitFor(() => {
      expect(screen.getByText('🟢 Streaming')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Stop Stream/i })).toBeInTheDocument();
    });

    // Cleanup
    delete global.WebSocket;
  });
});
