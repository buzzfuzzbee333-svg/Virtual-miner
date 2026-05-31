export type SourceEngine =
  | "PAYOUT_PULSE"
  | "SKILL_SURGE"
  | "GRANT_RADAR"
  | "FREEBIE_FORGE"
  | "HUSTLE_VALIDATOR"
  | "AFFILIATE_SPIKE_WATCH"
  | "LOCAL_ARBITRAGE_LENS"
  | "MICRO_TASK_MINER";

export type Category = "INSTANT_WIN" | "SHORT_TERM" | "LONG_TERM";
export type GeoScope = "US" | "EU" | "UK" | "GLOBAL";
export type InteractionStatus = "SAVED" | "DISMISSED" | "COMPLETED";

export interface Opportunity {
  id: string;
  sourceEngine: SourceEngine;
  title: string;
  description: string;
  url: string;
  tags: string[];
  category: Category;
  geoScope: GeoScope;
  scoreFriction: number;
  scorePayout: number;
  scoreTimeCost: number;
  scoreCompetition: number;
  scoreRisk: number;
  scoreDemand: number;
  scoreOverall: number;
  estimatedValue?: string;
  estimatedTime?: string;
  isCompound?: boolean;
  compoundEngines?: SourceEngine[];
  synergyBonus?: number;
  steps?: string[];
}

export interface UserInteractions {
  [opportunityId: string]: InteractionStatus;
}