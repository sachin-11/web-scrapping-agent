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
      const response = await fetch("http://localhost:8000/api/scrape", {
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
    <main className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center justify-start py-12 px-4 relative overflow-hidden font-sans">
      
      {/* Decorative Aurora Gradients */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-900/10 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-violet-900/10 blur-[130px] pointer-events-none" />

      {/* Floating dynamic Toast notification */}
      {toast && (
        <div
          className={`fixed top-6 right-6 z-50 flex items-center gap-3 py-3.5 px-5 rounded-xl border shadow-2xl transition-all duration-300 transform translate-y-0 animate-bounce ${
            toast.type === "success"
              ? "bg-zinc-900/90 border-emerald-500/30 text-emerald-400"
              : toast.type === "error"
              ? "bg-zinc-900/90 border-rose-500/30 text-rose-400"
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

      {/* Main dashboard content container */}
      <div className="max-w-4xl w-full space-y-12 relative z-10">
        
        {/* Branding header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500/10 to-violet-500/10 border border-indigo-500/20 px-4 py-1.5 rounded-full text-xs font-bold tracking-wide uppercase text-indigo-400 shadow-inner">
            ⚡ Web Intelligence Agent
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-zinc-200 to-zinc-400">
            Web Scraper AI Agent
          </h1>
          <p className="text-sm md:text-base text-zinc-500 max-w-xl mx-auto">
            Automatically crawl multi-page websites using Playwright, process records with GPT-4o-mini, resize product photos, and compile structured Excel spreadsheets.
          </p>
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
        
        {/* Footnotes */}
        <div className="text-center text-xs text-zinc-700 pt-6">
          Web Scraper Agent Framework • Core API v1.0.0
        </div>
      </div>
    </main>
  );
}
