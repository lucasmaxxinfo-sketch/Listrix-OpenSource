import React from "react";

/**
 * DeckStage — animated DJ-deck stage (spinning vinyl + neon rings + EQ).
 * Used as the visual centerpiece on the sign-in screen.
 */
export const DeckStage = ({ className = "" }) => (
  <div className={`relative mx-auto h-44 w-44 sm:h-52 sm:w-52 ${className}`} data-testid="deck-stage" aria-hidden="true">
    {/* outer neon halo */}
    <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle,rgba(255,122,26,0.35),rgba(255,122,26,0.08)_55%,transparent_70%)] blur-xl" />

    {/* amber deck ring */}
    <div className="absolute inset-1 rounded-full border-2 border-[#ff7a1a] shadow-[0_0_26px_rgba(255,122,26,0.55),inset_0_0_18px_rgba(255,122,26,0.18)]" />

    {/* vinyl (spinning) */}
    <div className="lx-vinyl absolute inset-4 rounded-full bg-[radial-gradient(circle_at_32%_30%,#26262b,#0a0a0d_65%,#040405)] shadow-[inset_0_0_22px_rgba(0,0,0,0.9),0_0_0_1px_rgba(255,176,106,0.35)]">
      <div className="lx-grooves absolute inset-0 rounded-full" />
      {/* label */}
      <div className="absolute left-1/2 top-1/2 flex h-12 w-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-[rgba(255,190,110,0.5)] bg-[radial-gradient(circle_at_35%_30%,#ffb06a,#e0701a_70%)] shadow-[0_0_18px_rgba(255,122,26,0.6)]">
        <span className="text-sm font-black text-[#1c0e02]">L</span>
      </div>
    </div>

    {/* spindle glow */}
    <div className="absolute left-1/2 top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#ffe3c2] shadow-[0_0_10px_rgba(255,190,110,0.95)]" />

    {/* equalizer */}
    <div className="absolute -bottom-3 left-1/2 flex -translate-x-1/2 items-end gap-[3px] rounded-md border border-[rgba(34,211,238,0.25)] bg-[rgba(8,10,12,0.8)] px-2 py-1 shadow-[0_0_14px_rgba(34,211,238,0.25)] backdrop-blur">
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <span key={i} className="eq-bar" style={{ animationDelay: `${i * 0.12}s` }} />
      ))}
    </div>
  </div>
);

export default DeckStage;
