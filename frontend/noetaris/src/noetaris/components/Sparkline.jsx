import React from "react";
export default function Sparkline({ data, w = 100, h = 30, color = "#2E9BFF" }) {
  if (!data?.length) return null;
  const min = Math.min(...data), max = Math.max(...data);
  const span = max - min || 1;
  const step = w / (data.length - 1);
  const pts = data.map((v, i) => `${i*step},${h - ((v-min)/span)*h}`).join(" ");
  return (
    <svg width={w} height={h} className="shrink-0">
      <defs>
        <linearGradient id={`sl-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.5"/>
          <stop offset="100%" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <polygon points={`0,${h} ${pts} ${w},${h}`} fill={`url(#sl-${color})`} opacity="0.5"/>
    </svg>
  );
}
