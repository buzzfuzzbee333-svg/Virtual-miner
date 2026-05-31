interface Props {
  label: string;
  value: number;
  inverted?: boolean;
}

export default function ScoreBar({ label, value, inverted }: Props) {
  const display = inverted ? 10 - value : value;
  const pct = (display / 10) * 100;
  const color = display >= 7 ? "#22c55e" : display >= 4 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex items-center gap-3">
      <span className="w-28 text-xs text-slate-400 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="w-5 text-right text-xs font-semibold" style={{ color }}>
        {display.toFixed(0)}
      </span>
    </div>
  );
}