import React from 'react';

export interface Settings {
  fileName: string;
  chapter: string;
  totalPages: number;
  intervalSec: number;
}

interface Props {
  settings: Settings;
  onChange: (s: Settings) => void;
  disabled: boolean;
}

export function CaptureSettings({ settings, onChange, disabled }: Props) {
  return (
    <div className="flex flex-col gap-4 p-5 border rounded-xl bg-zinc-900/80 backdrop-blur border-zinc-800 shadow-2xl w-full">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <span className="bg-blue-600 text-white text-sm w-6 h-6 flex items-center justify-center rounded-full">1</span>
        Configuration
      </h2>
      <div className="flex flex-col gap-2">
        <label className="text-sm font-semibold text-zinc-400">File Name</label>
        <input 
          type="text" 
          value={settings.fileName} 
          disabled={disabled}
          onChange={(e) => onChange({...settings, fileName: e.target.value})}
          className="bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all disabled:opacity-50" 
          placeholder="e.g. bookname"
        />
      </div>
      <div className="flex flex-col gap-2">
        <label className="text-sm font-semibold text-zinc-400">Chapter</label>
        <input 
          type="text" 
          value={settings.chapter} 
          disabled={disabled}
          onChange={(e) => onChange({...settings, chapter: e.target.value})}
          className="bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all disabled:opacity-50" 
          placeholder="e.g. 01"
        />
      </div>
      <div className="flex gap-4">
        <div className="flex flex-col gap-2 flex-1">
          <label className="text-sm font-semibold text-zinc-400">Total Pages</label>
          <input 
            type="number" 
            value={settings.totalPages} 
            disabled={disabled}
            onChange={(e) => onChange({...settings, totalPages: parseInt(e.target.value) || 0})}
            className="bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all disabled:opacity-50" 
          />
        </div>
        <div className="flex flex-col gap-2 flex-1">
          <label className="text-sm font-semibold text-zinc-400">Interval (sec)</label>
          <input 
            type="number" 
            step="0.5"
            disabled={disabled}
            value={settings.intervalSec} 
            onChange={(e) => onChange({...settings, intervalSec: parseFloat(e.target.value) || 1.5})}
            className="bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all disabled:opacity-50" 
          />
        </div>
      </div>
      <p className="text-xs text-zinc-500 mt-2">
        If page transitions are slow, please increase interval.
      </p>
    </div>
  );
}
