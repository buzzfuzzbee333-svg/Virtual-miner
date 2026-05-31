"use client";
import type { UserInteractions, InteractionStatus } from "./types";

const KEY = "apex_interactions";

export function getInteractions(): UserInteractions {
  if (typeof window === "undefined") return {};
  try { return JSON.parse(localStorage.getItem(KEY) || "{}"); }
  catch { return {}; }
}

export function setInteraction(id: string, status: InteractionStatus | null) {
  const current = getInteractions();
  if (status === null) { delete current[id]; } else { current[id] = status; }
  localStorage.setItem(KEY, JSON.stringify(current));
}