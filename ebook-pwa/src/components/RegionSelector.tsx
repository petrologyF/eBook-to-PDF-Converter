import React, { useRef, useState, useEffect } from 'react';
import { CaptureArea } from '@/hooks/useScreenCapture';

interface Props {
  stream: MediaStream;
  onConfirm: (area: CaptureArea, videoElement: HTMLVideoElement) => void;
  onCancel: () => void;
}

export function RegionSelector({ stream, onConfirm, onCancel }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [isDrawing, setIsDrawing] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startY, setStartY] = useState(0);
  const [currentX, setCurrentX] = useState(0);
  const [currentY, setCurrentY] = useState(0);
  const [hasSelection, setHasSelection] = useState(false);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  const handlePointerDown = (e: React.PointerEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setStartX(e.clientX - rect.left);
    setStartY(e.clientY - rect.top);
    setCurrentX(e.clientX - rect.left);
    setCurrentY(e.clientY - rect.top);
    setIsDrawing(true);
    setHasSelection(false);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    // Only capture while dragging
    if (!isDrawing || !containerRef.current || e.buttons !== 1) return;
    const rect = containerRef.current.getBoundingClientRect();
    setCurrentX(e.clientX - rect.left);
    setCurrentY(e.clientY - rect.top);
  };

  const handlePointerUp = () => {
    if (isDrawing) {
        setIsDrawing(false);
        setHasSelection(true);
    }
  };

  const calculateSelection = () => {
    const x = Math.min(startX, currentX);
    const y = Math.min(startY, currentY);
    const width = Math.abs(currentX - startX);
    const height = Math.abs(currentY - startY);
    return { x, y, width, height };
  };

  const handleConfirm = () => {
    if (!videoRef.current || !containerRef.current) return;
    const { x, y, width, height } = calculateSelection();
    
    // Scale coordinate to original video pixels using object-fill stretching logic
    const video = videoRef.current;
    const rect = video.getBoundingClientRect();
    const scaleX = video.videoWidth / rect.width;
    const scaleY = video.videoHeight / rect.height;

    const intrinsicArea: CaptureArea = {
      x: x * scaleX,
      y: y * scaleY,
      width: width * scaleX,
      height: height * scaleY
    };

    onConfirm(intrinsicArea, video);
  };

  const sel = calculateSelection();

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      <div className="flex bg-zinc-950 p-4 shrink-0 justify-between items-center text-white z-50 shadow-md">
        <div>
          <h3 className="font-bold text-xl text-blue-400">Select Capture Region</h3>
          <p className="text-zinc-400 text-sm">Draw a rectangle around the eBook pages, then confirm.</p>
        </div>
        <div className="flex gap-4">
          <button onClick={onCancel} className="px-6 py-2 bg-zinc-800 rounded-md font-medium hover:bg-zinc-700 transition">Cancel</button>
          <button 
            disabled={!hasSelection || sel.width < 10}
            onClick={handleConfirm} 
            className="px-6 py-2 bg-blue-600 text-white rounded-md font-bold hover:bg-blue-500 transition disabled:opacity-50"
          >
            Confirm Area
          </button>
        </div>
      </div>
      
      <div 
        ref={containerRef}
        className="relative flex-1 bg-black cursor-crosshair overflow-hidden select-none"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        <video 
          ref={videoRef} 
          autoPlay 
          muted 
          className="absolute inset-0 w-full h-full object-fill pointer-events-none" 
        />
        
        {/* Shadow Overlay */}
        <div className="absolute inset-0 bg-black/50 pointer-events-none" />
        
        {/* Selection Area Highlight */}
        {((isDrawing && calculateSelection().width > 0) || hasSelection) && (
          <div 
            className="absolute border-2 border-red-500 pointer-events-none shadow-[0_0_0_9999px_rgba(0,0,0,0.5)]"
            style={{
              left: Math.min(startX, currentX),
              top: Math.min(startY, currentY),
              width: Math.abs(currentX - startX),
              height: Math.abs(currentY - startY)
            }}
          >
              <div className="w-full h-full bg-transparent" />
          </div>
        )}
      </div>
    </div>
  );
}
