import React, { useEffect, useState } from "react";

/**
 * DeckScaler — fits the fixed 1280x800 Terilliom Deck canvas to any screen.
 * The Deck layout never changes (Terilliom Deck SDK rule); on phones and
 * portrait screens the whole tablet UI is scaled down and centred instead
 * of being hidden or squashed.
 */
export const DESIGN_W = 1280;
export const DESIGN_H = 800;

export const DeckScaler = ({ children }) => {
  const [fit, setFit] = useState({ scale: 1, x: 0, y: 0 });

  useEffect(() => {
    const compute = () => {
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const scale = Math.min(1, vw / DESIGN_W, vh / DESIGN_H);
      setFit({
        scale,
        x: (vw - DESIGN_W * scale) / 2,
        y: (vh - DESIGN_H * scale) / 2,
      });
    };
    compute();
    window.addEventListener("resize", compute);
    window.addEventListener("orientationchange", compute);
    return () => {
      window.removeEventListener("resize", compute);
      window.removeEventListener("orientationchange", compute);
    };
  }, []);

  return (
    <div className="lx-scaler fixed inset-0 overflow-hidden" data-testid="deck-scaler">
      <div
        className="lx-scaler-canvas relative"
        style={{
          width: DESIGN_W,
          height: DESIGN_H,
          transform: `translate(${fit.x}px, ${fit.y}px) scale(${fit.scale})`,
          transformOrigin: "top left",
        }}
      >
        {children}
      </div>
    </div>
  );
};

export default DeckScaler;
