import React, { useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import { getAllImages, clearImages, CapturedImage, db } from '@/lib/db';
import { Trash2 } from 'lucide-react';

export interface GalleryRef {
  refresh: () => void;
}

export const ImageGallery = forwardRef<GalleryRef, unknown>((props, ref) => {
  const [images, setImages] = useState<(CapturedImage & { url: string })[]>([]);

  const loadImages = async () => {
    const data = await getAllImages();
    const withUrls = data.map(img => ({
      ...img,
      url: URL.createObjectURL(img.blob)
    }));
    setImages(withUrls);
  };

  useImperativeHandle(ref, () => ({
    refresh: () => loadImages()
  }));

  useEffect(() => {
    loadImages();
  }, []);

  const handleDelete = async (id: number) => {
    await db.images.delete(id);
    loadImages();
  };
  
  const handleClearAll = async () => {
    if (window.confirm("Are you sure you want to delete all captured images?")) {
      await clearImages();
      loadImages();
    }
  };

  return (
    <div className="flex flex-col w-full h-full p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2 text-white">
           <span className="bg-blue-600 text-white text-sm w-6 h-6 flex items-center justify-center rounded-full">3</span>
           Preview Gallery
        </h2>
        <div className="flex gap-3">
          <button onClick={loadImages} className="text-sm px-4 py-2 bg-zinc-800 text-zinc-300 rounded hover:bg-zinc-700 transition font-medium">Refresh</button>
          <button onClick={handleClearAll} className="px-4 py-2 text-sm bg-red-500/10 text-red-500 border border-red-500/20 rounded hover:bg-red-500/20 transition font-medium">Clear All</button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 pb-10">
          {images.map(img => (
            <div key={img.id} className="relative group bg-zinc-900 rounded-lg overflow-hidden flex flex-col items-center justify-center p-2 border border-zinc-800 shadow-md transition-transform hover:scale-105">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={img.url} alt={`Page ${img.pageNumber}`} className="object-cover w-full h-32 rounded bg-zinc-950" />
              <div className="w-full text-center text-xs text-zinc-400 mt-2 font-medium">Page {img.pageNumber}</div>
              
              <button 
                onClick={() => img.id && handleDelete(img.id)}
                className="absolute top-2 right-2 p-1.5 bg-red-600 rounded-md opacity-0 group-hover:opacity-100 transition-opacity text-white hover:bg-red-500 shadow-lg"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {images.length === 0 && (
            <div className="col-span-full h-48 flex items-center justify-center text-zinc-500 border-2 border-dashed border-zinc-800 rounded-xl bg-zinc-900/30">
              No images yet. Start a capture session.
            </div>
          )}
        </div>
      </div>
    </div>
  );
});
ImageGallery.displayName = "ImageGallery";
