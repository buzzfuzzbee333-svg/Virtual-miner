"use client";
import { useState, useCallback } from "react";
import type { Category } from "@/lib/types";
import { OPPORTUNITIES } from "@/lib/opportunities";
import { getInteractions } from "@/lib/storage";
import OpportunityCard from "@/components/OpportunityCard";
import Link from "next/link";

const TABS: { label: string; value: Category; icon: string }[] = [
  { label: "Instant Wins", value: "INSTANT_WIN", icon: "⚡" },
  { label: "Short-Term", value: "SHORT_TERM", icon: "📈" },
  { label: "Long-Term", value: "LONG_TERM", icon: "🎯" },
];

export default function FeedPage() {
  const [activeTab, setActiveTab] = useState<Category>("INSTANT_WIN");
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => setTick((n) => n + 1), []);

  const interactions = getInteractions();
  const topAlerts = OPPORTUNITIES.filter(
    (o) => o.scoreOverall >= 8.5 && interactions[o.id] !== "DISMISSED"
  ).slice(0, 2);

  const tabOpps = OPPORTUNITIES.filter(
    (o) => o.category === activeTab && interactions[o.id] !== "DISMISSED"
  ).sort((a, b) => b.scoreOverall - a.scoreOverall);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="sticky top-0 z-20 bg-slate-950/95 backdrop-blur border-b border-slate-800 px-4">
        <div className="max-w-lg mx-auto flex items-center justify-between py-3">
          <div>
            <h1 className="text-base font-bold tracking-tight">
              <span className="text-indigo-400">APEX</span>
              <span className="text-amber-400">-</span>
              <span>Fusion</span>
            </h1>
            <p className="text-[10px] text-slate-500 -mt-0.5">Opportunity Intelligence</p>
          </div>
          <Link
            href="/saved"
            className="text-xs text-slate-400 bg-slate-800 rounded-full px-3 py-1.5 hover:bg-slate-700 transition-colors"
          >
            Saved
          </Link>
        </div>
        <div className="max-w-lg mx-auto flex gap-1 pb-2">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={`flex-1 py-2 rounded-xl text-xs font-semibold transition-all ${
                activeTab === tab.value
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 py-4 flex flex-col gap-3">
        {activeTab === "INSTANT_WIN" && topAlerts.length > 0 && (
          <div className="rounded-2xl bg-amber-500/5 border border-amber-500/20 p-3">
            <p className="text-[10px] font-bold text-amber-400 uppercase tracking-widest mb-2">
              High-Score Alerts
            </p>
            {topAlerts.map((o) => (
              <Link
                key={o.id}
                href={`/opportunity/${o.id}`}
                className="flex items-center justify-between py-1.5 hover:opacity-80 transition-opacity"
              >
                <span className="text-xs text-slate-200 line-clamp-1 flex-1">{o.title}</span>
                <span className="text-xs font-bold text-amber-400 ml-2">{o.scoreOverall}</span>
              </Link>
            ))}
          </div>
        )}
        {tabOpps.length === 0 ? (
          <div className="text-center py-16 text-slate-500 text-sm">
            No opportunities here — check another tab or reset dismissals in Settings.
          </div>
        ) : (
          tabOpps.map((opp) => (
            <OpportunityCard key={`${opp.id}-${tick}`} opp={opp} onInteract={refresh} />
          ))
        )}
      </main>
    </div>
  );
}