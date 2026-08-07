import React, { useRef, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import DeckLogo from "@/components/DeckLogo";
import { DECK_SEGMENTS, getActiveModule, COMMAND_TO } from "./modules";

const C = 200; // svg centre
const OUTER_R = 186;
const SEG_R1 = 128;
const SEG_R2 = 186;
const LABEL_R = 159;
const SEGMENTS = DECK_SEGMENTS.length; // 8
const STEP = 360 / SEGMENTS;

function polar(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function wedgePath(a0, a1) {
  const start = polar(C, C, SEG_R1, a0);
  const end = polar(C, C, SEG_R2, a1);
  const mid = polar(C, C, SEG_R1, a1);
  const large = a1 - a0 > 180 ? 1 : 0;
  return [
    `M ${start.x.toFixed(2)} ${start.y.toFixed(2)}`,
    `L ${end.x.toFixed(2)} ${end.y.toFixed(2)}`,
    `A ${SEG_R2} ${SEG_R2} 0 ${large} 1 ${polar(C, C, SEG_R2, a0).x.toFixed(2)} ${polar(C, C, SEG_R2, a0).y.toFixed(2)}`,
    `A ${SEG_R1} ${SEG_R1} 0 ${large} 0 ${mid.x.toFixed(2)} ${mid.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

/**
 * Deck — the signature Terilliom interaction component.
 * Fixed diameter, rings, segments, glow, rotation, zoom, drag and click behaviour.
 */
export const Deck = ({ compact = false }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const activeModule = getActiveModule(location.pathname);
  const [drag, setDrag] = useState(0);
  const [zoom, setZoom] = useState(1);
  const dragState = useRef(null);
  const wrapRef = useRef(null);

  const onPointerDown = useCallback((e) => {
    e.preventDefault();
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    dragState.current = {
      x: e.clientX,
      y: e.clientY,
      cx: rect.left + rect.width / 2,
      cy: rect.top + rect.height / 2,
      base: dragState.current ? dragState.current.base : 0,
    };
  }, []);

  const onPointerMove = useCallback((e) => {
    const s = dragState.current;
    if (!s) return;
    const a = (Math.atan2(e.clientY - s.cy, e.clientX - s.cx) * 180) / Math.PI;
    const b = (Math.atan2(s.y - s.cy, s.x - s.cx) * 180) / Math.PI;
    setDrag(s.base + (a - b));
  }, []);

  const onPointerUp = useCallback(() => {
    dragState.current = null;
  }, []);

  const onWheel = useCallback((e) => {
    setZoom((z) => Math.min(1.3, Math.max(0.72, z - e.deltaY * 0.001)));
  }, []);

  const segments = SEGMENTS;
  const labelOffset = STEP / 2;

  return (
    <div
      data-testid="central-deck"
      ref={wrapRef}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onWheel={onWheel}
      className="lx-deck relative mx-auto select-none"
      style={{
        width: "min(460px, 100%, 46vh)",
        aspectRatio: "1 / 1",
        minHeight: compact ? 240 : 300,
      }}
      aria-label="Terilliom Deck — drag to rotate, scroll to zoom, tap a segment to navigate"
    >
      {/* stage glow */}
      <div className="absolute left-1/2 top-1/2 h-[92%] w-[92%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(30,26,18,0.55),rgba(0,0,0,0.9)_62%)] shadow-[0_0_90px_rgba(255,180,90,0.14),inset_0_0_70px_rgba(0,0,0,0.85)]" />
      <div className="absolute left-1/2 top-1/2 h-[86%] w-[86%] -translate-x-1/2 -translate-y-1/2 rounded-full lx-rainbow-halo" />

      {/* interactive layer — scales with scroll zoom, rotates with drag */}
      <div
        className="absolute inset-0"
        style={{ transform: `scale(${zoom}) rotate(${drag}deg)` }}
      >
        <svg viewBox="0 0 400 400" className="h-full w-full drop-shadow-[0_0_22px_rgba(0,0,0,0.8)]">
          <defs>
            <radialGradient id="deckPlate" cx="0.5" cy="0.42" r="0.75">
              <stop offset="0" stopColor="#191622" />
              <stop offset="0.55" stopColor="#0c0a12" />
              <stop offset="1" stopColor="#050408" />
            </radialGradient>
            <linearGradient id="deckRimRainbow" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#ff6a5e" />
              <stop offset="0.25" stopColor="#ffe14d" />
              <stop offset="0.5" stopColor="#5ee08a" />
              <stop offset="0.75" stopColor="#3ec8f2" />
              <stop offset="1" stopColor="#ff6ec7" />
            </linearGradient>
          </defs>

          {/* static plate */}
          <circle cx={C} cy={C} r={OUTER_R} fill="url(#deckPlate)" stroke="url(#deckRimRainbow)" strokeWidth="2.5" />
          <circle cx={C} cy={C} r={SEG_R1 - 6} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />

          {/* static segments — dim, active one glows */}
          {DECK_SEGMENTS.map((seg, i) => {
            const a0 = i * STEP;
            const active = seg.id === activeModule || (seg.id === "command" && location.pathname === COMMAND_TO);
            return (
              <g key={seg.id} onClick={() => navigate(seg.to)} className="deck-seg cursor-pointer"
                data-testid={`deck-segment-${seg.id}`} role="link" aria-label={seg.label}>
                <path
                  d={wedgePath(a0, a0 + STEP)}
                  fill={seg.color}
                  fillOpacity={active ? 0.32 : 0.1}
                  stroke={seg.color}
                  strokeWidth={active ? 2 : 1}
                  strokeOpacity={active ? 0.95 : 0.4}
                />
                {active && <path d={wedgePath(a0, a0 + STEP)} fill="none" stroke={seg.color} strokeWidth="3" strokeOpacity="0.6" />}
              </g>
            );
          })}

          {/* rotating pips ring (CSS spin) */}
          <g className="lx-ring-spin" style={{ transformOrigin: "200px 200px" }}>
            {DECK_SEGMENTS.map((seg, i) => {
              const p = polar(C, C, SEG_R1 - 12, i * STEP + STEP / 2);
              return <circle key={seg.id} cx={p.x} cy={p.y} r="3.4" fill={seg.color} opacity="0.9" />;
            })}
          </g>

          {/* reverse dashed mid ring */}
          <circle className="lx-ring-spin-rev" cx={C} cy={C} r={108} fill="none"
            stroke="rgba(255,255,255,0.22)" strokeWidth="1.2" strokeDasharray="3 7"
            style={{ transformOrigin: "200px 200px" }} />

          {/* drag-group glow arcs */}
          <g transform={`rotate(${drag} 200 200)`}>
            <circle cx={C} cy={C} r={SEG_R2 + 10} fill="none" stroke="rgba(255,190,90,0.28)" strokeWidth="1.2" strokeDasharray="1 10" />
          </g>
        </svg>

        {/* static segment labels */}
        {DECK_SEGMENTS.map((seg, i) => {
          const mid = i * STEP + labelOffset;
          const p = polar(C, C, LABEL_R, mid);
          const active = seg.id === activeModule || (seg.id === "command" && location.pathname === COMMAND_TO);
          return (
            <button
              key={seg.id}
              data-testid={`deck-label-${seg.id}`}
              onClick={() => navigate(seg.to)}
              className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider transition-all duration-150 lx-deck-touch"
              style={{
                left: `${(p.x / 400) * 100}%`,
                top: `${(p.y / 400) * 100}%`,
                color: seg.color,
                borderColor: active ? seg.color : "rgba(255,255,255,0.14)",
                background: active ? `rgba(0,0,0,0.72)` : "rgba(6,6,10,0.6)",
                boxShadow: active ? `0 0 14px ${seg.color}66, inset 0 0 8px ${seg.color}22` : "none",
              }}
            >
              {seg.label}
            </button>
          );
        })}

        {/* centre hub — the app's heart */}
        <button
          data-testid="deck-center"
          onClick={() => navigate(COMMAND_TO)}
          className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full lx-deck-touch"
          aria-label="Open command center"
        >
          <DeckLogo size={88} rainbow />
        </button>
      </div>

      {/* deck status strip */}
      <div className="pointer-events-none absolute bottom-1 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-full border border-white/10 bg-black/55 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-white/55 backdrop-blur">
        <span className="h-1.5 w-1.5 rounded-full bg-[#5ee08a] shadow-[0_0_8px_#5ee08a] lx-pulse-2s" />
        Terilliom Deck · Listrix
      </div>
    </div>
  );
};

export default Deck;
