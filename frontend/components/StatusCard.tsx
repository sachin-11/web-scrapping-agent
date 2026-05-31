"use client";

import React from "react";

interface StatusCardProps {
  currentStep: number; // 0: Idle, 1: Browser, 2: Crawling, 3: LLM, 4: Excel, 5: Complete
  error?: string | null;
}

export default function StatusCard({ currentStep, error }: StatusCardProps) {
  const steps = [
    { id: 1, label: "Initialize Headless Browser", desc: "Setting up secure Chromium environment via Playwright" },
    { id: 2, label: "Crawl & Clean Page Text", desc: "Reading DOM nodes, extracting text, and parsing links" },
    { id: 3, label: "LLM Structured Analysis", desc: "Using GPT-4o-mini to convert raw text into schema-matched JSON" },
    { id: 4, label: "Compile & Format Excel", desc: "Resizing images, freezing panes, styling sheets, and writing result" },
  ];

  if (currentStep === 0 && !error) return null;

  return (
    <div className="backdrop-blur-md bg-zinc-900/40 border border-zinc-800/80 rounded-2xl p-6 shadow-2xl space-y-6 relative overflow-hidden">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">Agent Execution Status</h3>
          <p className="text-xs text-zinc-500 mt-0.5">Real-time processing feedback from Playwright & OpenAI</p>
        </div>
        {currentStep < 5 && !error && (
          <div className="flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full text-xs font-semibold animate-pulse border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Active
          </div>
        )}
        {currentStep === 5 && (
          <div className="flex items-center gap-1.5 bg-indigo-500/10 text-indigo-400 px-3 py-1 rounded-full text-xs font-semibold border border-indigo-500/20">
            ✓ Finished
          </div>
        )}
        {error && (
          <div className="flex items-center gap-1.5 bg-rose-500/10 text-rose-400 px-3 py-1 rounded-full text-xs font-semibold border border-rose-500/20">
            ⚠ Failed
          </div>
        )}
      </div>

      <div className="space-y-4">
        {steps.map((step) => {
          const isDone = currentStep > step.id;
          const isActive = currentStep === step.id;
          const isPending = currentStep < step.id;

          return (
            <div
              key={step.id}
              className={`flex items-start gap-4 p-3 rounded-xl border transition-all duration-300 ${
                isActive
                  ? "bg-zinc-950/60 border-indigo-500/40 shadow-lg shadow-indigo-500/5"
                  : isDone
                  ? "bg-zinc-950/20 border-zinc-800/40 opacity-70"
                  : "bg-transparent border-transparent opacity-40"
              }`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {isDone ? (
                  <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                ) : isActive ? (
                  <div className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center border border-indigo-500/40 animate-pulse">
                    <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  </div>
                ) : (
                  <div className="w-6 h-6 rounded-full bg-zinc-800 text-zinc-500 flex items-center justify-center border border-zinc-700/50 text-xs font-semibold">
                    {step.id}
                  </div>
                )}
              </div>

              <div>
                <span className={`block text-sm font-semibold transition-colors duration-300 ${
                  isActive ? "text-indigo-400" : isDone ? "text-zinc-300" : "text-zinc-500"
                }`}>
                  {step.label}
                </span>
                <span className="block text-xs text-zinc-500 mt-0.5">{step.desc}</span>
              </div>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm p-4 rounded-xl space-y-1">
          <div className="font-bold flex items-center gap-1.5">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Error Details:
          </div>
          <div className="text-xs break-words">{error}</div>
        </div>
      )}
    </div>
  );
}
