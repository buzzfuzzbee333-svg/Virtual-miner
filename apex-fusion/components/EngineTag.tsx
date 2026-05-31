import { ENGINE_LABELS, ENGINE_COLORS } from "@/lib/scoring";
import type { SourceEngine } from "@/lib/types";

interface Props {
  engine: SourceEngine;
  small?: boolean;
}

export default function EngineTag({ engine, small }: Props) {
  const color = ENGINE_COLORS[engine] ?? "#6b7280";
  const label = ENGINE_LABELS[engine] ?? engine;
  return (
    <span
      className={`inline-flex items-center rounded-full font-semibold ${small ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-0.5 text-xs"}`}
      style={{ backgroundColor: `${color}22`, color }}
    >
      {label}
    </span>
  );
}