import React from "react";

/**
 * DeckLogo — neon DJ-deck turntable mark for Listrix.
 * Pure SVG (no external assets) so it works offline and self-hosted.
 */
export const DeckLogo = ({ size = 36, withWordmark = false, rainbow = false, className = "" }) => (
  <span className={`inline-flex items-center gap-2.5 ${className}`}>
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      role="img"
    >
      <defs>
        <linearGradient id="lxRainbowStroke" x1="4" y1="4" x2="60" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#ff6a5e" />
          <stop offset="0.2" stopColor="#ffb648" />
          <stop offset="0.4" stopColor="#ffe14d" />
          <stop offset="0.6" stopColor="#5ee08a" />
          <stop offset="0.8" stopColor="#3ec8f2" />
          <stop offset="1" stopColor="#ff6ec7" />
        </linearGradient>
        <linearGradient id="lxPlate" x1="8" y1="6" x2="56" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#2a2016" />
          <stop offset="0.55" stopColor="#171008" />
          <stop offset="1" stopColor="#0c0804" />
        </linearGradient>
        <linearGradient id="lxVinyl" x1="20" y1="16" x2="44" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#1d1d20" />
          <stop offset="0.5" stopColor="#0c0c0f" />
          <stop offset="1" stopColor="#050506" />
        </linearGradient>
        <radialGradient id="lxSpindle" cx="0.35" cy="0.3" r="1" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#fff2dd" />
          <stop offset="1" stopColor="#e08a3c" />
        </radialGradient>
        <filter id="lxGlowA" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="2.6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="lxGlowC" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="2.2" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* deck plate */}
      <rect x="2.5" y="2.5" width="59" height="59" rx="15" fill="url(#lxPlate)" stroke={rainbow ? "url(#lxRainbowStroke)" : "rgba(255,190,110,0.4)"} strokeWidth="1.6" />
      <rect x="6" y="6" width="52" height="52" rx="12" fill="none" stroke="rgba(34,211,238,0.16)" strokeWidth="1" />

      {/* left deck (amber) */}
      <circle cx="24" cy="25" r="14" fill="url(#lxVinyl)" />
      <circle cx="24" cy="25" r="14" fill="none" stroke="#ff7a1a" strokeWidth="2.4" opacity="0.95" filter="url(#lxGlowA)" />
      <circle cx="24" cy="25" r="11" fill="none" stroke="rgba(255,176,106,0.4)" strokeWidth="0.8" strokeDasharray="2 2.4" />
      <circle cx="24" cy="25" r="8" fill="none" stroke="rgba(255,176,106,0.3)" strokeWidth="0.8" strokeDasharray="1.6 2.6" />
      <circle cx="24" cy="25" r="2.6" fill="url(#lxSpindle)" filter="url(#lxGlowA)" />

      {/* right deck (cyan) */}
      <circle cx="43" cy="25" r="10" fill="url(#lxVinyl)" />
      <circle cx="43" cy="25" r="10" fill="none" stroke="#22d3ee" strokeWidth="2" opacity="0.9" filter="url(#lxGlowC)" />
      <circle cx="43" cy="25" r="7" fill="none" stroke="rgba(125,238,251,0.35)" strokeWidth="0.8" strokeDasharray="1.8 2.4" />
      <circle cx="43" cy="25" r="2" fill="#c9f6ff" filter="url(#lxGlowC)" />

      {/* mixer rail / equalizer */}
      <line x1="12" y1="42" x2="52" y2="42" stroke="rgba(34,211,238,0.25)" strokeWidth="1.2" />
      {[15, 19, 23, 27, 31].map((x, i) => (
        <rect
          key={x}
          x={x}
          y={45 - (i % 3 === 0 ? 5 : i % 3 === 1 ? 9 : 7)}
          width="2.6"
          height={i % 3 === 0 ? 5 : i % 3 === 1 ? 9 : 7}
          rx="1.3"
          fill={i % 2 === 0 ? "#ff9d4d" : "#22d3ee"}
          opacity="0.9"
        />
      ))}
      <line x1="12" y1="54" x2="52" y2="54" stroke="rgba(255,190,110,0.18)" strokeWidth="1.2" />
    </svg>
    {withWordmark && (
      <span className="leading-tight">
        <span className="neon-title block text-lg font-black tracking-tight">LISTRIX</span>
        <span className="block text-[9px] uppercase tracking-[0.3em] text-muted-foreground">Business OS</span>
      </span>
    )}
  </span>
);

export default DeckLogo;
