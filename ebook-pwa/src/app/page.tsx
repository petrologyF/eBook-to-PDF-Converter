'use client';
import { useState, useRef, useEffect } from 'react';
import { CaptureSettings, Settings } from '@/components/CaptureSettings';
import { RegionSelector } from '@/components/RegionSelector';
import { ImageGallery, GalleryRef } from '@/components/ImageGallery';
import { useScreenCapture, CaptureArea } from '@/hooks/useScreenCapture';
import { usePdfGenerator } from '@/hooks/usePdfGenerator';
import { Download, MonitorPlay, BookOpen } from 'lucide-react';

export default function Home() {
  const [settings, setSettings] = useState<Settings>({
    fileName: 'book',
    chapter: '01',
    totalPages: 20,
    intervalSec: 1.5,
  });

  const {
    stream,
    isCapturing,
    progress,
    startScreenShare,
    stopScreenShare,
    startCaptureLoop,
    stopCaptureLoop
  } = useScreenCapture();

  const { generatePdf, isGenerating } = usePdfGenerator();
  const galleryRef = useRef<GalleryRef>(null);

  const [showRegionSelector, setShowRegionSelector] = useState(false);

  useEffect(() => {
    if (stream && !isCapturing && !showRegionSelector) {
        setShowRegionSelector(true);
    }
  }, [stream, isCapturing, showRegionSelector]);

  const handleStartShare = () => {
    startScreenShare();
  };

  const handleRegionConfirm = (area: CaptureArea, videoElement: HTMLVideoElement) => {
    setShowRegionSelector(false);
    startCaptureLoop(videoElement, area, settings.totalPages, settings.intervalSec);
  };

  const handleRegionCancel = () => {
    stopScreenShare();
    setShowRegionSelector(false);
  };

  const prevProgress = useRef(progress);
  useEffect(() => {
    if (progress > prevProgress.current) {
        galleryRef.current?.refresh();
        prevProgress.current = progress;
    }
  }, [progress]);

  const progressPercent = Math.min(100, Math.round((progress / settings.totalPages) * 100)) || 0;

  return (
    <main className="min-h-screen flex flex-col items-center bg-[#09090b] text-white p-4 sm:p-8 font-sans">
      <div className="max-w-7xl w-full flex flex-col gap-8 flex-1 mt-4">
        
        {/* Header */}
        <div className="text-center md:text-left flex items-center gap-4 border-b border-zinc-800 pb-6 mb-2">
            <div className="p-3 bg-blue-600/20 text-blue-400 rounded-2xl shadow-lg ring-1 ring-blue-500/50">
                <BookOpen size={30} />
            </div>
            <div>
                <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-400">eBook to PDF</h1>
                <p className="text-zinc-500 font-medium">PWA Tool to Capture and Convert Web eBooks to PDF</p>
            </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start relative">
            
            {/* Sidebar Left */}
            <div className="lg:col-span-1 flex flex-col gap-6 sticky top-8">
                <CaptureSettings 
                    settings={settings} 
                    onChange={setSettings} 
                    disabled={isCapturing || !!stream} 
                />

                <div className="bg-zinc-900/80 backdrop-blur border border-zinc-800 rounded-xl p-5 shadow-2xl flex flex-col gap-4">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <span className="bg-blue-600 text-white text-sm w-6 h-6 flex items-center justify-center rounded-full">2</span>
                        Action
                    </h2>

                    {!isCapturing ? (
                        <button 
                            onClick={handleStartShare}
                            disabled={settings.totalPages <= 0 || !!stream}
                            className="bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 disabled:text-zinc-400 text-white py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-all shadow-[0_0_20px_rgba(37,99,235,0.2)] hover:shadow-[0_0_25px_rgba(37,99,235,0.4)]"
                        >
                            <MonitorPlay size={20} />
                            Start Capture
                        </button>
                    ) : (
                        <div className="flex flex-col gap-4 bg-zinc-950/50 p-4 rounded-lg border border-zinc-800">
                            <button 
                                onClick={stopCaptureLoop}
                                className="bg-red-600/10 text-red-500 border border-red-500/20 hover:bg-red-600/20 py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition"
                            >
                                Stop Capture
                            </button>
                            <div className="text-sm font-semibold flex justify-between text-zinc-300">
                                <span>Capturing...</span>
                                <span>{progress} / {settings.totalPages}</span>
                            </div>
                            <div className="w-full bg-zinc-800 rounded-full h-2.5 overflow-hidden">
                                <div className="bg-blue-500 h-2.5 transition-all duration-300 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.6)]" style={{ width: `${progressPercent}%` }} />
                            </div>
                        </div>
                    )}

                    <hr className="border-zinc-800 my-1" />

                    <button 
                        onClick={() => generatePdf(settings.fileName, settings.chapter)}
                        disabled={isGenerating || isCapturing}
                        className="bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 border border-zinc-700 hover:border-zinc-600 text-white py-3 px-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-all shadow-md"
                    >
                        {isGenerating ? (
                            <span className="animate-pulse">Generating PDF...</span>
                        ) : (
                            <>
                                <Download size={20} />
                                Export PDF
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Main Area */}
            <div className="lg:col-span-3 bg-zinc-900/40 rounded-2xl border border-zinc-800/80 h-[650px] overflow-hidden shadow-2xl ring-1 ring-white/5 backdrop-blur-sm">
                <ImageGallery ref={galleryRef} />
            </div>

        </div>

      </div>

      {showRegionSelector && stream && (
          <RegionSelector 
            stream={stream} 
            onConfirm={handleRegionConfirm} 
            onCancel={handleRegionCancel} 
          />
      )}
    </main>
  );
}
