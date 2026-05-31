"use client";
import { useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { OPPORTUNITIES } from "@/lib/opportunities";
import { getInteractions, setInteraction } from "@/lib/storage";
import ScoreRing from "@/components/ScoreRing";
import EngineTag from "@/components/EngineTag";

export default function SavedPage() {
  const [tick, setTick] = useState(0);
  const router = useRouter();
  const refresh = useCallback(() => setTick((n) => n + 1), []);
  const interactions = getInteractions();
  const saved = OPPORTUNITIES.filter((o) => interactions[o.id] === "SAVED");
  const completed = OPPORTUNITIES.filter((o) => interactions[o.id] === "COMPLETED");

  function remove(id: string) { setInteraction(id, "DISMISSED"); refresh(); }
  function markComplete(id: string) { setInteraction(id, "COMPLETED"); refresh(); }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="sticky top-0 z-20 bg-slate-950/95 backdrop-blur border-b border-slate-800 px-4 py-3">
        <div className="max-w-lg mx-auto flex items-center gap-3">
          <button onClick={() => router.back()} className="text-slate-400 hover:text-white text-sm">← Back</button>
          <span className="text-sm font-semibold text-slate-200">Saved Opportunities</span>
        </div>
      </header>
      <main className="max-w-lg mx-auto px-4 py-4 flex flex-col gap-6">
        <section>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Active ({saved.length})</p>
          {saved.length === 0 ? (
            <p className="text-sm text-slate-600 py-4">No saved opportunities yet. Browse the feed and save ones you want to act on.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {saved.map((opp) => (
                <div key={opp.id} className="rounded-2xl bg-slate-900 border border-slate-800 p-3 flex items-center gap-3">
                  <ScoreRing score={opp.scoreOverall} size={44} />
                  <div className="flex-1 min-w-0">
                    <Link href={`/opportunity/${opp.id}`} className="text-xs font-semibold text-white line-clamp-1 hover:text-indigo-400 transition-colors">{opp.title}</Link>
                    <EngineTag engine={opp.sourceEngine} small />
                  </div>
                  <div className="flex flex-col gap-1">
                    <button onClick={() => markComplete(opp.id)} className="text-[10px] px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">Done</button>
                    <button onClick={() => remove(opp.id)} className="text-[10px] px-2 py-1 rounded-lg bg-slate-800 text-slate-500 hover:text-slate-300">Remove</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
        {completed.length > 0 && (
          <section>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Completed ({completed.length})</p>
            <div className="flex flex-col gap-2">
              {completed.map((opp) => (
                <div key={opp.id} className="rounded-2xl bg-slate-900/50 border border-slate-800/50 p-3 flex items-center gap-3 opacity-60">
                  <ScoreRing score={opp.scoreOverall} size={44} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-400 line-clamp-1">{opp.title}</p>
                    <span className="text-[10px] text-emerald-500 font-semibold">✓ Completed</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}