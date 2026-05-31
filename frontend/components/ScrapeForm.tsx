"use client";

import React, { useState } from "react";

interface ScrapeFormProps {
  onSubmit: (formData: {
    url: string;
    instruction: string;
    download_images: boolean;
    max_pages: number;
  }) => void;
  isLoading: boolean;
}

export default function ScrapeForm({ onSubmit, isLoading }: ScrapeFormProps) {
  const [url, setUrl] = useState("");
  const [instruction, setInstruction] = useState("");
  const [downloadImages, setDownloadImages] = useState(false);
  const [maxPages, setMaxPages] = useState(1);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    onSubmit({
      url,
      instruction: instruction || "Extract all visible tables, listings, or details.",
      download_images: downloadImages,
      max_pages: maxPages,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="backdrop-blur-md bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-6 shadow-2xl space-y-6 relative overflow-hidden"
    >
      {/* Decorative gradient light */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

      <div>
        <label className="block text-sm font-semibold text-zinc-300 mb-2">
          Target Website URL
        </label>
        <div className="relative group">
          <input
            type="url"
            required
            disabled={isLoading}
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example-shop.com/products"
            className="w-full bg-zinc-950/60 border border-zinc-800 focus:border-indigo-500/80 focus:ring-2 focus:ring-indigo-500/20 text-white rounded-xl py-3 px-4 outline-none transition duration-300 text-sm group-hover:border-zinc-700"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold text-zinc-300 mb-2">
          What data to extract? (Instructions)
        </label>
        <textarea
          disabled={isLoading}
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="e.g. Extract name, price, rating, reviews, image_url, and description of all listing items."
          rows={4}
          className="w-full bg-zinc-950/60 border border-zinc-800 focus:border-indigo-500/80 focus:ring-2 focus:ring-indigo-500/20 text-white rounded-xl py-3 px-4 outline-none transition duration-300 text-sm resize-none"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Toggle images */}
        <div className="flex items-center justify-between p-4 bg-zinc-950/40 border border-zinc-800/40 rounded-xl">
          <div>
            <span className="block text-sm font-semibold text-zinc-300">
              Download Images
            </span>
            <span className="block text-xs text-zinc-500 mt-0.5">
              Download, resize, and embed product photos
            </span>
          </div>
          <button
            type="button"
            disabled={isLoading}
            onClick={() => setDownloadImages(!downloadImages)}
            className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${
              downloadImages ? "bg-indigo-600" : "bg-zinc-800"
            }`}
          >
            <div
              className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-300 ${
                downloadImages ? "translate-x-6" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {/* Number Input Max Pages */}
        <div className="flex flex-col justify-center p-4 bg-zinc-950/40 border border-zinc-800/40 rounded-xl">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold text-zinc-300">
              Max Pages
            </span>
            <span className="text-xs bg-indigo-500/20 text-indigo-400 font-medium px-2 py-0.5 rounded-full">
              {maxPages} Page(s)
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            disabled={isLoading}
            value={maxPages}
            onChange={(e) => setMaxPages(parseInt(e.target.value))}
            className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading || !url.trim()}
        className={`w-full py-3 px-6 rounded-xl font-semibold text-white shadow-lg transition duration-300 flex items-center justify-center gap-2 ${
          isLoading || !url.trim()
            ? "bg-zinc-800 text-zinc-500 cursor-not-allowed border border-zinc-700/30"
            : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 hover:shadow-indigo-500/25 border border-indigo-500/30 cursor-pointer"
        }`}
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin h-5 w-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>Analyzing & Crawling...</span>
          </>
        ) : (
          <>
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <span>Initialize Scraper Agent</span>
          </>
        )}
      </button>
    </form>
  );
}
