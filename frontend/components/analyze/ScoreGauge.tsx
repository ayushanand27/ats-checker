"use client";

import { useEffect, useState } from "react";

interface ScoreGaugeProps {
  score: number;
  label: string;
  hint?: string;
}

function arcColor(score: number): string {
  if (score >= 75) return "#6B8F7A";
  if (score >= 50) return "#8B7355";
  return "#9B6B6B";
}

function scoreVerdict(score: number): string {
  if (score >= 85) return "Excellent";
  if (score >= 75) return "Strong";
  if (score >= 60) return "Good";
  if (score >= 45) return "Fair";
  return "Needs work";
}

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(cx: number, cy: number, r: number, start: number, end: number) {
  const s = polar(cx, cy, r, end);
  const e = polar(cx, cy, r, start);
  const large = end - start <= 180 ? 0 : 1;
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 0 ${e.x} ${e.y}`;
}

const ARC_START = 135;
const ARC_SWEEP = 270;
const CX = 100;
const CY = 108;
const R = 70;
const TRACK = "#252830";
const MUTED = "#7B8394";

export function ScoreGauge({ score, label, hint }: ScoreGaugeProps) {
  const [mounted, setMounted] = useState(false);
  const color = arcColor(score);
  const scoreEnd = ARC_START + (score / 100) * ARC_SWEEP;
  const needleTip = polar(CX, CY, R - 2, mounted ? scoreEnd : ARC_START);

  useEffect(() => {
    const t = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(t);
  }, []);

  const majorTicks = [0, 25, 50, 75, 100];
  const minorTicks = Array.from({ length: 21 }, (_, i) => i * 5).filter(
    (t) => t % 25 !== 0,
  );

  return (
    <div
      className="flex flex-col items-center py-2"
      aria-label={`${label}: ${score} out of 100`}
    >
      <div className="relative h-[210px] w-[220px]">
        <svg
          width="220"
          height="210"
          viewBox="0 0 200 175"
          className="overflow-visible"
          role="img"
          aria-hidden
        >
          {/* Outer ring */}
          <circle
            cx={CX}
            cy={CY}
            r={R + 14}
            fill="none"
            stroke={TRACK}
            strokeWidth={1}
            opacity={0.6}
          />

          {/* Minor tick marks */}
          {minorTicks.map((t) => {
            const angle = ARC_START + (t / 100) * ARC_SWEEP;
            const inner = polar(CX, CY, R - 2, angle);
            const outer = polar(CX, CY, R + 2, angle);
            return (
              <line
                key={`minor-${t}`}
                x1={inner.x}
                y1={inner.y}
                x2={outer.x}
                y2={outer.y}
                stroke={TRACK}
                strokeWidth={1}
                opacity={0.7}
              />
            );
          })}

          {/* Major tick marks + labels */}
          {majorTicks.map((t) => {
            const angle = ARC_START + (t / 100) * ARC_SWEEP;
            const inner = polar(CX, CY, R - 8, angle);
            const outer = polar(CX, CY, R + 6, angle);
            const labelPos = polar(CX, CY, R + 18, angle);
            const isActive = score >= t;
            return (
              <g key={t}>
                <line
                  x1={inner.x}
                  y1={inner.y}
                  x2={outer.x}
                  y2={outer.y}
                  stroke={isActive ? color : TRACK}
                  strokeWidth={2}
                  strokeLinecap="round"
                  className="transition-colors duration-micro"
                />
                <text
                  x={labelPos.x}
                  y={labelPos.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill={isActive ? color : MUTED}
                  fontSize="9"
                  fontFamily="var(--font-plex), IBM Plex Sans, sans-serif"
                  className="tabular-nums transition-colors duration-micro"
                >
                  {t}
                </text>
              </g>
            );
          })}

          {/* Track arc */}
          <path
            d={arcPath(CX, CY, R, ARC_START, ARC_START + ARC_SWEEP)}
            fill="none"
            stroke={TRACK}
            strokeWidth={7}
            strokeLinecap="round"
          />

          {/* Score arc */}
          <path
            d={arcPath(CX, CY, R, ARC_START, mounted ? scoreEnd : ARC_START)}
            fill="none"
            stroke={color}
            strokeWidth={7}
            strokeLinecap="round"
            className="transition-all duration-[400ms] ease-out"
            style={{ filter: `drop-shadow(0 0 6px ${color}40)` }}
          />

          {/* Needle hub */}
          <circle cx={CX} cy={CY} r={5} fill="#13151A" stroke={TRACK} strokeWidth={1.5} />
          <circle cx={CX} cy={CY} r={2.5} fill={color} className="transition-colors duration-micro" />

          {/* Needle tip indicator */}
          <circle
            cx={needleTip.x}
            cy={needleTip.y}
            r={3.5}
            fill={color}
            stroke="#13151A"
            strokeWidth={1}
            className="transition-all duration-[400ms] ease-out"
          />
        </svg>

        <div className="absolute inset-x-0 bottom-4 flex flex-col items-center">
          <span className="tabular-nums text-[2.75rem] font-semibold leading-none tracking-tight text-text">
            {score.toFixed(1)}
          </span>
          <span className="mt-1 text-[11px] uppercase tracking-widest text-text-muted">
            / 100
          </span>
        </div>
      </div>

      <p className="mt-1 text-center text-sm font-medium text-text">{label}</p>
      <p className="font-serif text-base tracking-tight text-accent">{scoreVerdict(score)}</p>
      {hint && (
        <p className="mt-2 max-w-xs text-center text-xs leading-relaxed text-text-muted">
          {hint}
        </p>
      )}
    </div>
  );
}
