"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import type { Opportunity, InteractionStatus } from "@/lib/types";
import { getInteractions, setInteraction } from "@/lib/storage";
import ScoreRing from "./ScoreRing";
import EngineTag from "./EngineTag";

interface Props { opp: Opportunity; onInteract?: () => void; }

export default function OpportunityCard({ opp, onInteract }: Props) {
  const [status, setStatus] = useState<InteractionStatus | null>(null);

  useEffect(() => {
    setStatus(getInteractions()[opp.id] ?? null);
  }, [opp.id]);

  function interact(s: InteractionStatus) {
    setInteraction(opp.id, s);
    setStatus(s);
    onInteract?.();
  }

  if (status === "DISMISSED") return null;

  return (
    <div className="relative rounded-2xl bg-slate-900 border p-4 flex flex-col gap-3"
      style={{ borderColor: opp.isCompound ? "#f59e0b55" : "#1e293b" }}>
      {opp.isCompound && (
        <div className="absolute top-3 right-3 bg-amber-500/10 border border-amber-500/30 rounded-full px-2 py-0.5">
          <span className="text-amber-400 text-[10px] font-bold tracking-wide">FUSION</span>
        </div>
      )}
      <div className="flex items-start gap-3 pr-16">
        <ScoreRing score={opp.scoreOverall} />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white leading-snug line-clamp-2">{opp.title}</h3>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <EngineTag engine={opp.sourceEngine} small />
            {opp.geoScope !== "GLOBAL" && <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">{opp.geoScope}</span>}
          </div>
        </div>
      </div>
      <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">{opp.description}</p>
      {(opp.estimatedValue || opp.estimatedTime) && (
        <div className="flex gap-3">
          {opp.estimatedValue && <div className="flex items-center gap-1.5"><span className="text-[10px] text-slate-500">Value</span><span className="text-xs font-semibold text-emerald-400">{opp.estimatedValue}</span></div>}
          {opp.estimatedTime && <div className="flex items-center gap-1.5"><span className="text-[10px] text-slate-500">Time</span><span className="text-xs font-semibold text-sky-400">{opp.estimatedTime}</span></div>}
        </div>
      )}
      <div className="flex items-center gap-2 mt-1">
        <Link href={`/opportunity/${opp.id}`} className="flex-1 text-center text-xs font-semibold py-2 rounded-xl bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors">View Details</Link>
        {status === "SAVED" ? (
          <button onClick={() => interact("COMPLETED")} className="px-3 py-2 rounded-xl bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">Complete</button>
        ) : status === "COMPLETED" ? (
          <span className="px-3 py-2 rounded-xl bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">Done ✓</span>
        ) : (
          <button onClick={() => interact("SAVED")} className="px-3 py-2 rounded-xl bg-indigo-500/10 text-indigo-400 text-xs font-semibold border border-indigo-500/20">Save</button>
        )}
        <button onClick={() => interact("DISMISSED")} className="px-3 py-2 rounded-xl bg-slate-800 text-slate-500 text-xs hover:text-slate-300">✕</button>
      </div>
    </div>
  );
}