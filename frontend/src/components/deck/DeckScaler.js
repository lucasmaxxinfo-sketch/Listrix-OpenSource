import React, { createContext, useContext, useEffect, useState } from "react";

/**
 * DeckScaler — fits the fixed 1280x800 Terilliom Deck canvas to any screen.
 * The Deck layout never changes (Terilliom Deck SDK rule).
 *
 * Landscape (or tablet portrait): the full tablet UI is scaled to stretch and
 * fit the whole screen, centred with the design proportions intact.
 *
 * Portrait phones: the Deck is split across the screen (buttons | wheel |
 * live metrics) and scaled to fit, so the app stays fully usable upright.
 */
export const DESIGN_W = 1280;
export const DESIGN_H = 800;

const DeckModeContext = createContext({ portrait: false });
export const useDeckMode = () => useContext(DeckModeContext);

export const DeckScaler = ({ children }) => {
  const [mode, setMode] = useState("landscape");
  const [fit, setFit] = useState({ scale: 1, x: 0, y: 0 });

  useEffect(() => {
    const compute = () => {
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const portraitPhone = vh > vw && vw < 768;

      if (portraitPhone) {
        setMode("portrait");
        return;
      }

      setMode("landscape");
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

  if (mode === "portrait") {
    return (
      <DeckModeContext.Provider value={{ portrait: true }}>
        <div className="lx-portrait-host fixed inset-0 overflow-hidden" data-testid="deck-scaler-portrait">
          {children}
        </div>
      </DeckModeContext.Provider>
    );
  }

  return (
    <DeckModeContext.Provider value={{ portrait: false }}>
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
    </DeckModeContext.Provider>
  );
};

export default DeckScaler;
