"use client";
import { scoreColor } from "@/lib/scoring";

interface Props { score: number; size?: number; }

export default function ScoreRing({ score, size = 52 }: Props) {
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const fill = (score / 10) * circ;
  const color = scoreColor(score);
  return (
    <svg width={size} height={size} className="shrink-0">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth={4} />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={4}
        strokeDasharray={`${fill} ${circ}`} strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`} />
      <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle"
        fontSize={size < 48 ? 11 : 13} fontWeight="700" fill={color}>
        {score.toFixed(1)}
      </text>
    </svg>
  );
}