import React from "react";

// Original NOETARIS CoGen wordmark. The emblem is a stylized "N" shaped like a
// forged mountain ridge — material/color inspired by metallic blue/red, drawn from scratch.
export const Logo = ({ size = 32, withWord = true, muted = false }) => (
  <div className="flex items-center gap-3" data-testid="brand-logo">
    <svg
      width={size} height={size}
      viewBox="0 0 48 48" fill="none"
      style={{ filter: muted ? "none" : "drop-shadow(0 4px 18px rgba(46,155,255,.35))" }}
    >
      <defs>
        <linearGradient id="metal-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#dfe9f3" />
          <stop offset=".5" stopColor="#7fa5c7" />
          <stop offset="1" stopColor="#1f3a58" />
        </linearGradient>
        <linearGradient id="metal-grad-2" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#2E9BFF" />
          <stop offset="1" stopColor="#C41E2A" />
        </linearGradient>
      </defs>
      {/* ridge back */}
      <path d="M6 42 L6 10 L14 10 L24 28 L24 10 L30 10 L30 42 L24 42 L14 24 L14 42 Z" fill="url(#metal-grad)" opacity=".92"/>
      {/* front edge */}
      <path d="M18 42 L18 18 L24 28 L24 10 L34 10 L34 42 L42 42 L42 10" stroke="url(#metal-grad-2)" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      {/* luminous bar */}
      <rect x="36" y="12" width="2" height="28" fill="url(#metal-grad-2)" />
    </svg>
    {withWord && (
      <div className="leading-none">
        <div className="font-display text-[15px] tracking-wide text-[color:var(--n-text)]">
          Noetaris <span className="text-[color:var(--n-cyan)]">CoGen</span>
        </div>
        <div className="text-[10px] uppercase tracking-[0.2em] text-[color:var(--n-text-subtle)]">
          Powered by NSAI
        </div>
      </div>
    )}
  </div>
);

export default Logo;
