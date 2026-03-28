import { useState, useRef, useCallback } from 'react';
import { addImage } from '@/lib/db';

export interface CaptureArea {
  x: number;
  y: number;
  width: number;
  height: number;
}

export function useScreenCapture() {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [progress, setProgress] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startScreenShare = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getDisplayMedia({
        video: { displaySurface: 'window' },
        audio: false,
      });
      setStream(mediaStream);
      
      mediaStream.getVideoTracks()[0].onended = () => {
        stopScreenShare();
      };
    } catch (err) {
      console.error("Error sharing screen:", err);
    }
  };

  const stopScreenShare = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    stopCaptureLoop();
  };

  const startCaptureLoop = useCallback(async (
    videoElement: HTMLVideoElement,
    area: CaptureArea, // area in Intrinsic Video Coordinates
    totalPages: number,
    intervalSec: number
  ) => {
    setIsCapturing(true);
    setProgress(0);
    
    let currentPage = 1;

    const captureFrame = async () => {
      if (currentPage > totalPages) {
        stopCaptureLoop();
        return;
      }

      const canvas = document.createElement('canvas');
      canvas.width = area.width;
      canvas.height = area.height;
      const ctx = canvas.getContext('2d');
      if (ctx && videoElement) {
        ctx.drawImage(
          videoElement,
          area.x,
          area.y,
          area.width,
          area.height,
          0,
          0,
          area.width,
          area.height
        );
        
        canvas.toBlob(async (blob) => {
          if (blob) {
            await addImage(blob, currentPage);
            setProgress(currentPage);
            currentPage++;
          }
        }, 'image/png');
      }
    };

    // To allow user to switch to the window, maybe we should not capture immediately.
    // The first execution will happen after intervalSec
    timerRef.current = setInterval(captureFrame, intervalSec * 1000);
  }, []);

  const stopCaptureLoop = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsCapturing(false);
  };

  return {
    stream,
    isCapturing,
    progress,
    startScreenShare,
    stopScreenShare,
    startCaptureLoop,
    stopCaptureLoop
  };
}
