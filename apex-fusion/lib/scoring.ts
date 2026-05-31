import type { Opportunity, Category } from "./types";

const WEIGHTS = {
  payout: 0.30,
  friction: 0.25,
  demand: 0.15,
  timeCost: 0.15,
  competition: 0.10,
  risk: 0.05,
};

export function computeOverallScore(opp: Omit<Opportunity, "scoreOverall" | "category">): number {
  const score =
    WEIGHTS.payout * opp.scorePayout +
    WEIGHTS.friction * (10 - opp.scoreFriction) +
    WEIGHTS.demand * opp.scoreDemand +
    WEIGHTS.timeCost * (10 - opp.scoreTimeCost) +
    WEIGHTS.competition * (10 - opp.scoreCompetition) -
    WEIGHTS.risk * opp.scoreRisk;
  return Math.min(10, Math.max(0, Math.round(score * 10) / 10));
}

export function classifyCategory(timeCost: number, friction: number): Category {
  if (timeCost <= 3 && friction <= 3) return "INSTANT_WIN";
  if (timeCost <= 6) return "SHORT_TERM";
  return "LONG_TERM";
}

export function scoreColor(score: number): string {
  if (score >= 8) return "#22c55e";
  if (score >= 6) return "#f59e0b";
  return "#ef4444";
}

export const ENGINE_LABELS: Record<string, string> = {
  PAYOUT_PULSE: "Payout Pulse",
  SKILL_SURGE: "Skill Surge",
  GRANT_RADAR: "Grant Radar",
  FREEBIE_FORGE: "Freebie Forge",
  HUSTLE_VALIDATOR: "Hustle Validator",
  AFFILIATE_SPIKE_WATCH: "Affiliate Spike",
  LOCAL_ARBITRAGE_LENS: "Local Arbitrage",
  MICRO_TASK_MINER: "Micro-Task",
};

export const ENGINE_COLORS: Record<string, string> = {
  PAYOUT_PULSE: "#6366f1",
  SKILL_SURGE: "#8b5cf6",
  GRANT_RADAR: "#10b981",
  FREEBIE_FORGE: "#f59e0b",
  HUSTLE_VALIDATOR: "#3b82f6",
  AFFILIATE_SPIKE_WATCH: "#ec4899",
  LOCAL_ARBITRAGE_LENS: "#f97316",
  MICRO_TASK_MINER: "#06b6d4",
};