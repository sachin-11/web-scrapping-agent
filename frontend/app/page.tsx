"use client";

import React, { useState, useEffect } from "react";
import ScrapeForm from "../components/ScrapeForm";
import StatusCard from "../components/StatusCard";
import PreviewTable from "../components/PreviewTable";
import DownloadButton from "../components/DownloadButton";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0: Idle, 1: Browser, 2: Scraped, 3: LLM, 4: Excel, 5: Complete
  const [error, setError] = useState<string | null>(null);
  const [scrapedData, setScrapedData] = useState<any[] | null>(null);
  const [excelUrl, setExcelUrl] = useState<string | null>(null);
  const [totalRecords, setTotalRecords] = useState(0);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);

  // Auto-dismiss toasts after 5 seconds
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        setToast(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const triggerToast = (message: string, type: "success" | "error" | "info") => {
    setToast({ message, type });
  };

  const handleStartScrape = async (formData: {
    url: string;
    instruction: string;
    download_images: boolean;
    max_pages: number;
  }) => {
    setIsLoading(true);
    setError(null);
    setScrapedData(null);
    setExcelUrl(null);
    
    // Step 1: Initializing Browser
    setCurrentStep(1);
    triggerToast("Starting Web Scraper Agent session...", "info");

    // Simulate progress visual changes for smooth micro-animations
    const progressTimer1 = setTimeout(() => setCurrentStep(2), 2000); // Transition to Crawling after 2s
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
      const response = await fetch(`${apiBase}/api/scrape`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      // Clear the early progress timer so the real steps coordinate
      clearTimeout(progressTimer1);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error (Status: ${response.status})`);
      }

      // Simulate LLM processing step
      setCurrentStep(3);
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Simulate Excel step
      setCurrentStep(4);
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const result = await response.json();

      if (result.success) {
        setScrapedData(result.preview_data);
        setExcelUrl(result.excel_url);
        setTotalRecords(result.total_records);
        setCurrentStep(5);
        triggerToast(`Successfully scraped ${result.total_records} items!`, "success");
      } else {
        throw new Error(result.error || "Scraping completed but returned failure.");
      }

    } catch (err: any) {
      console.error(err);
      setError(err.message || "An unexpected network error occurred.");
      setCurrentStep(0);
      triggerToast(err.message || "Scraping failed.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center justify-between relative overflow-hidden font-sans">
      
      {/* 🌌 Premium Grid & Aurora Backgrounds */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f1f23_1px,transparent_1px),linear-gradient(to_bottom,#1f1f23_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-35 pointer-events-none" />
      
      {/* Glowing colorful auroras */}
      <div className="absolute top-[-10%] left-[5%] w-[550px] h-[550px] rounded-full bg-indigo-600/10 blur-[130px] pointer-events-none animate-pulse" />
      <div className="absolute top-[20%] right-[-5%] w-[450px] h-[450px] rounded-full bg-fuchsia-600/10 blur-[130px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-[-10%] left-[20%] w-[500px] h-[500px] rounded-full bg-cyan-600/5 blur-[120px] pointer-events-none" />

      {/* 📌 Fixed Glassmorphic Header / Navigation bar */}
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-zinc-950/80 border-b border-zinc-900/60 px-6 py-4 flex items-center justify-between max-w-full">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-indigo-500 to-fuchsia-500 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
            ⚡
          </div>
          <span className="font-extrabold text-sm tracking-wider uppercase bg-clip-text text-transparent bg-gradient-to-r from-white via-zinc-200 to-zinc-400">
            Scraper<span className="text-indigo-400">Agent</span>
          </span>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1.5 bg-zinc-900 border border-zinc-800/80 px-3 py-1 rounded-full text-[10px] font-bold text-zinc-400">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            System Live
          </div>
          <a
            href="https://github.com/sachin-11/web-scrapping-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 px-3.5 py-1.5 rounded-xl text-zinc-300 font-semibold transition duration-150 flex items-center gap-2"
          >
            <svg className="w-3.5 h-3.5 text-zinc-400" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
            </svg>
            GitHub
          </a>
        </div>
      </header>

      {/* Floating dynamic Toast notification */}
      {toast && (
        <div
          className={`fixed top-24 right-6 z-50 flex items-center gap-3 py-3.5 px-5 rounded-2xl border shadow-2xl transition-all duration-300 transform translate-y-0 animate-bounce backdrop-blur-lg ${
            toast.type === "success"
              ? "bg-emerald-950/80 border-emerald-500/30 text-emerald-400"
              : toast.type === "error"
              ? "bg-rose-950/80 border-rose-500/30 text-rose-400"
              : "bg-zinc-900/90 border-indigo-500/30 text-indigo-400"
          }`}
        >
          <div className="flex-shrink-0">
            {toast.type === "success" && (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            {toast.type === "error" && (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            {toast.type === "info" && (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </div>
          <span className="text-sm font-semibold">{toast.message}</span>
        </div>
      )}

      {/* Main dashboard content container (Padded vertically to accommodate fixed headers/footers) */}
      <div className="max-w-4xl w-full space-y-12 relative z-10 pt-28 pb-20 px-2 flex-grow">
        
        {/* Branding header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500/10 to-fuchsia-500/10 border border-indigo-500/20 px-4 py-1.5 rounded-full text-xs font-bold tracking-wider uppercase text-indigo-400 shadow-lg shadow-indigo-500/5 animate-pulse">
            ✨ Next-Gen Web Intelligence Agent
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-zinc-100 to-zinc-400">AI Web Scraper </span>
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-violet-400 to-fuchsia-400">Agent</span>
          </h1>
          <p className="text-xs md:text-sm text-zinc-500 max-w-xl mx-auto leading-relaxed">
            Crawls websites dynamically via headless **Playwright** chromium engines, extracts clean data patterns with **GPT-4o-mini**, processes product images, and auto-compiles styled spreadsheets.
          </p>
        </div>

        {/* 🚀 Interactive System Statistics Banner */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-2xl border border-zinc-800/60 bg-zinc-900/10 backdrop-blur-md">
          <div className="text-center p-2 border-r border-zinc-800/40">
            <span className="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Scraper Engine</span>
            <span className="text-xs font-semibold text-zinc-300 mt-1 block">Playwright (Async)</span>
          </div>
          <div className="text-center p-2 border-r border-zinc-800/40">
            <span className="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider">AI Processor</span>
            <span className="text-xs font-semibold text-indigo-400 mt-1 block">GPT-4o-mini</span>
          </div>
          <div className="text-center p-2 border-r border-zinc-800/40">
            <span className="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Output Format</span>
            <span className="text-xs font-semibold text-emerald-400 mt-1 block">Excel (.xlsx)</span>
          </div>
          <div className="text-center p-2">
            <span className="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Agent Status</span>
            <span className="text-xs font-semibold text-cyan-400 mt-1 block flex items-center justify-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              Online
            </span>
          </div>
        </div>

        {/* Home grids */}
        <div className="grid grid-cols-1 gap-8">
          {/* 1. Scrape Form */}
          <ScrapeForm onSubmit={handleStartScrape} isLoading={isLoading} />

          {/* 2. Status Card */}
          <StatusCard currentStep={currentStep} error={error} />

          {/* 3. Successful Downloader */}
          {excelUrl && !isLoading && (
            <DownloadButton totalRecords={totalRecords} />
          )}

          {/* 4. Preview Data Table */}
          {scrapedData && !isLoading && (
            <PreviewTable data={scrapedData} />
          )}
        </div>
      </div>
      
      {/* 📌 Styled Production Footer */}
      <footer className="w-full backdrop-blur-md bg-zinc-950/80 border-t border-zinc-900/60 py-6 px-6 relative z-10 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-xs text-zinc-500">
          © 2026 ScraperAgent. Powered by Playwright & OpenAI.
        </div>
        <div className="flex items-center gap-6 text-xs text-zinc-400 font-semibold">
          <a href="/docs" className="hover:text-white transition duration-150">API Docs</a>
          <a href="/terms" className="hover:text-white transition duration-150">Terms</a>
          <a href="/privacy" className="hover:text-white transition duration-150">Privacy</a>
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            All Systems Operational
          </div>
        </div>
      </footer>
    </main>
  );
}
