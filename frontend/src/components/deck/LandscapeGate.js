import React, { useState } from "react";
import { RotateCcw, X } from "lucide-react";

const DISMISS_KEY = "listrix:landscape-hint-dismissed";

/**
 * Landscape hint — Listrix is a forced-landscape tablet app. The DeckScaler
 * fits the full tablet UI onto any screen, so portrait phones get a small
 * dismissible hint instead of a blocking rotate screen.
 */
export const LandscapeGate = () => {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem(DISMISS_KEY) === "1";
    } catch {
      return false;
    }
  });

  if (dismissed) return null;

  const dismiss = () => {
    setDismissed(true);
    try {
      sessionStorage.setItem(DISMISS_KEY, "1");
    } catch {}
  };

  return (
    <div
      data-testid="landscape-gate"
      className="lx-rotate-pill"
      role="note"
    >
      <RotateCcw size={15} className="lx-rotate-hint shrink-0 text-[#ffb648]" />
      <span className="min-w-0">
        <span className="block text-[11px] font-black uppercase tracking-[0.18em] text-white">Tablet preview</span>
        <span className="block text-[11px] leading-snug text-white/60">
          Listrix is a landscape app — this view is scaled to fit your screen. Rotate your device for full size.
        </span>
      </span>
      <button
        type="button"
        onClick={dismiss}
        aria-label="Dismiss hint"
        className="deck-ico flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[hsl(var(--tp-border))] text-white/70 transition-colors duration-150 hover:text-white"
      >
        <X size={15} />
      </button>
    </div>
  );
};

export default LandscapeGate;
