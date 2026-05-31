"use client";

import React from "react";

interface DownloadButtonProps {
  totalRecords: number;
}

export default function DownloadButton({ totalRecords }: DownloadButtonProps) {
  const handleDownload = () => {
    // Navigate straight to download route on backend
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
    window.open(`${apiBase}/api/download-excel`, "_blank");
  };

  return (
    <div className="backdrop-blur-md bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-6 shadow-2xl relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6">
      {/* Glow lights */}
      <div className="absolute top-0 left-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="text-center md:text-left space-y-1">
        <h3 className="text-lg font-bold text-white">Extraction Successful!</h3>
        <p className="text-xs text-zinc-500">
          Ready to save. Compiled with auto column sizing and clean formatting.
        </p>
        <div className="flex flex-wrap items-center gap-3 justify-center md:justify-start pt-2">
          <span className="text-xs bg-emerald-500/20 text-emerald-400 font-semibold px-3 py-1 rounded-full border border-emerald-500/30">
            {totalRecords} Total Items
          </span>
          <span className="text-xs bg-zinc-800 text-zinc-400 font-semibold px-3 py-1 rounded-full border border-zinc-700/50">
            Sheet: Scraped Data
          </span>
        </div>
      </div>

      <button
        onClick={handleDownload}
        className="w-full md:w-auto px-8 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold rounded-xl shadow-lg hover:shadow-emerald-500/25 border border-emerald-500/30 hover:scale-[1.02] transform transition duration-300 flex items-center justify-center gap-3 cursor-pointer group"
      >
        <svg
          className="w-5 h-5 text-white transform group-hover:translate-y-0.5 transition-transform duration-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2.5"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
          />
        </svg>
        <span>Download Excel Spreadsheet</span>
      </button>
    </div>
  );
}
