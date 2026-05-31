"use client";
import { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { OPPORTUNITIES } from "@/lib/opportunities";
import { getInteractions, setInteraction } from "@/lib/storage";
import type { InteractionStatus } from "@/lib/types";
import ScoreRing from "@/components/ScoreRing";
import ScoreBar from "@/components/ScoreBar";
import EngineTag from "@/components/EngineTag";

export default function DetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const opp = OPPORTUNITIES.find((o) => o.id === id);
  const [status, setStatus] = useState<InteractionStatus | null>(null);

  useEffect(() => {
    if (!opp) return;
    const interactions = getInteractions();
    setStatus(interactions[opp.id] ?? null);
  }, [opp]);

  if (!opp) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">Opportunity not found.</div>;

  function interact(s: InteractionStatus) {
    if (!opp) return;
    setInteraction(opp.id, s);
    setStatus(s);
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="sticky top-0 z-20 bg-slate-950/95 backdrop-blur border-b border-slate-800 px-4 py-3">
        <div className="max-w-lg mx-auto flex items-center gap-3">
          <button onClick={() => router.back()} className="text-slate-400 hover:text-white text-sm">← Back</button>
          <span className="text-sm font-semibold text-slate-200 line-clamp-1 flex-1">{opp.title}</span>
        </div>
      </header>
      <main className="max-w-lg mx-auto px-4 py-5 flex flex-col gap-5">
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5 flex items-center gap-4">
          <ScoreRing score={opp.scoreOverall} size={72} />
          <div className="flex-1">
            <h2 className="text-sm font-bold text-white leading-snug">{opp.title}</h2>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <EngineTag engine={opp.sourceEngine} />
              {opp.isCompound && <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-full px-2 py-0.5">FUSION ×{opp.synergyBonus}</span>}
              {opp.geoScope !== "GLOBAL" && <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">{opp.geoScope}</span>}
            </div>
            {(opp.estimatedValue || opp.estimatedTime) && (
              <div className="flex gap-4 mt-2">
                {opp.estimatedValue && <div><p className="text-[10px] text-slate-500">Est. Value</p><p className="text-sm font-bold text-emerald-400">{opp.estimatedValue}</p></div>}
                {opp.estimatedTime && <div><p className="text-[10px] text-slate-500">Time</p><p className="text-sm font-bold text-sky-400">{opp.estimatedTime}</p></div>}
              </div>
            )}
          </div>
        </div>
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4">
          <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">About</h3>
          <p className="text-sm text-slate-300 leading-relaxed">{opp.description}</p>
        </div>
        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4">
          <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Score Breakdown</h3>
          <div className="flex flex-col gap-2.5">
            <ScoreBar label="Payout" value={opp.scorePayout} />
            <ScoreBar label="Ease (friction)" value={opp.scoreFriction} inverted />
            <ScoreBar label="Speed" value={opp.scoreTimeCost} inverted />
            <ScoreBar label="Demand" value={opp.scoreDemand} />
            <ScoreBar label="Low Competition" value={opp.scoreCompetition} inverted />
            <ScoreBar label="Low Risk" value={opp.scoreRisk} inverted />
          </div>
          <p className="text-[10px] text-slate-600 mt-3">Payout (30%) · Ease (25%) · Speed (15%) · Demand (15%) · Competition (10%) · Risk (-5%)</p>
        </div>
        {opp.steps && opp.steps.length > 0 && (
          <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">How to Act</h3>
            <div className="flex flex-col gap-3">
              {opp.steps.map((step, i) => (
                <div key={i} className="flex gap-3">
                  <span className="w-5 h-5 rounded-full bg-indigo-600/20 border border-indigo-600/40 flex items-center justify-center text-[10px] font-bold text-indigo-400 shrink-0 mt-0.5">{i + 1}</span>
                  <p className="text-sm text-slate-300 leading-snug">{step}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="flex flex-wrap gap-1.5">
          {opp.tags.map((tag) => <span key={tag} className="text-[10px] px-2 py-1 rounded-full bg-slate-800 text-slate-500 font-medium">#{tag}</span>)}
        </div>
        <div className="flex flex-col gap-2 pb-8">
          {status === "COMPLETED" ? (
            <div className="w-full py-3 rounded-2xl bg-emerald-500/10 text-emerald-400 text-sm font-semibold text-center border border-emerald-500/20">Marked as Complete ✓</div>
          ) : (
            <button onClick={() => interact("COMPLETED")} className="w-full py-3 rounded-2xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-500 transition-colors">Mark as Complete</button>
          )}
          {status !== "SAVED" && status !== "COMPLETED" && (
            <button onClick={() => interact("SAVED")} className="w-full py-3 rounded-2xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-500 transition-colors">Save Opportunity</button>
          )}
          <button onClick={() => { interact("DISMISSED"); router.back(); }} className="w-full py-3 rounded-2xl bg-slate-800 text-slate-400 text-sm font-semibold hover:bg-slate-700 transition-colors">Dismiss</button>
        </div>
      </main>
    </div>
  );
}