import React from "react";
import { RotateCcw } from "lucide-react";

/**
 * Forced-landscape gate.
 * The Terilliom Deck layout is fixed landscape; portrait screens get
 * a rotate prompt instead of a broken vertical layout.
 */
export const LandscapeGate = () => (
  <div
    data-testid="landscape-gate"
    className="lx-landscape-gate fixed inset-0 z-[999] hidden flex-col items-center justify-center gap-5 bg-[#07050c] px-8 text-center text-white"
  >
    <span className="flex h-20 w-20 items-center justify-center rounded-full border-2 border-[#ffb648] text-[#ffb648] shadow-[0_0_40px_rgba(255,182,72,0.45)] lx-rotate-hint">
      <RotateCcw size={36} />
    </span>
    <div>
      <p className="text-xl font-black uppercase tracking-widest">Rotate your device</p>
      <p className="mt-1 text-sm text-white/60">Listrix runs in landscape — turn your screen sideways to continue.</p>
    </div>
    <p className="max-w-xs text-[11px] leading-relaxed text-white/35">Terilliom Deck SDK · The interface is fixed. Only the business function changes.</p>
  </div>
);

export default LandscapeGate;
