import React, { useRef, useState, useCallback, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { DECK_SEGMENTS } from "./modules";

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

/** Which deck segment the current route belongs to (so the knob wakes up on the right mode). */
export function segmentIndexForPath(pathname) {
  const hit = DECK_SEGMENTS.findIndex((s) => pathname === s.to || pathname.startsWith(`${s.to}/`));
  if (hit >= 0) return hit;
  if (pathname === "/") return DECK_SEGMENTS.findIndex((s) => s.id === "command");
  return 0;
}

function angleAt(cx, cy, x, y) {
  return (Math.atan2(y - cy, x - cx) * 180) / Math.PI;
}

/**
 * DeckLcd — the LCD panel above the wheel. Fixed by the Deck SDK: it always
 * shows the option under the knob marker, and updates live as the wheel turns.
 */
export const DeckLcd = ({ selected, compact = false }) => {
  const seg = DECK_SEGMENTS[selected];
  const Icon = seg.icon;
  return (
    <div
      data-testid="deck-lcd"
      aria-live="polite"
      className={`lx-lcd relative w-full max-w-[340px] overflow-hidden rounded-xl border ${
        compact ? "px-3 py-1.5" : "px-4 py-2"
      }`}
    >
      <div className="relative z-10 font-mono">
        <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-[0.3em] text-[#7dffa9]/75">
          <span>Listrix · Deck</span>
          <span>{String(selected + 1).padStart(2, "0")} / {String(SEGMENTS).padStart(2, "0")}</span>
        </div>
        <div className="mt-1 flex items-center gap-2">
          <span
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md border bg-black/40"
            style={{ color: seg.color, borderColor: `${seg.color}55`, boxShadow: `0 0 12px ${seg.color}33` }}
          >
            <Icon size={compact ? 13 : 15} />
          </span>
          <span
            className={`truncate font-black uppercase tracking-[0.14em] ${compact ? "text-[13px]" : "text-[15px]"}`}
            style={{ color: seg.color, textShadow: `0 0 12px ${seg.color}88` }}
          >
            {seg.label}
          </span>
          <span className="ml-auto hidden shrink-0 text-[9px] uppercase tracking-[0.2em] text-[#7dffa9]/55 sm:block">
            Press knob ↓
          </span>
        </div>
        <div className="mt-1.5 flex items-center gap-[3px]" aria-hidden="true">
          {DECK_SEGMENTS.map((s, i) => (
            <span
              key={s.id}
              className="h-1 flex-1 rounded-[2px] transition-all duration-150"
              style={{
                background: i === selected ? s.color : "rgba(255,255,255,0.12)",
                boxShadow: i === selected ? `0 0 8px ${s.color}` : "none",
                height: i === selected ? 6 : 4,
              }}
            />
          ))}
        </div>
      </div>
      <div className="lx-lcd-scan pointer-events-none absolute inset-0 z-0" />
      <div className="lx-lcd-glass pointer-events-none absolute inset-0 z-20" />
    </div>
  );
};

/**
 * DeckControl — the knob + LCD cluster (the signature Terilliom interaction).
 * Turning the wheel cycles the eight deck options on the LCD, the segment
 * buttons light up for the selected mode, and pressing the knob opens it.
 */
export const DeckControl = ({ compact = false, size }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const wrapRef = useRef(null);

  const [selected, setSelected] = useState(() => segmentIndexForPath(location.pathname));
  const [spinDeg, setSpinDeg] = useState(() => segmentIndexForPath(location.pathname) * STEP);
  const [snapping, setSnapping] = useState(false);
  const selectedRef = useRef(selected);
  const dragRef = useRef(null);
  const dragJustEndedRef = useRef(false);

  const applySelection = useCallback((idx, animate) => {
    const n = ((idx % SEGMENTS) + SEGMENTS) % SEGMENTS;
    selectedRef.current = n;
    setSelected(n);
    setSpinDeg(n * STEP);
    setSnapping(animate);
  }, []);

  // Keep the knob in sync when the app itself changes module (top nav, sidebar).
  useEffect(() => {
    applySelection(segmentIndexForPath(location.pathname), false);
  }, [location.pathname, applySelection]);

  const step = useCallback(
    (dir) => {
      applySelection(selectedRef.current + dir, true);
    },
    [applySelection]
  );

  const onPointerDown = useCallback((e) => {
    e.preventDefault();
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    dragRef.current = {
      x: e.clientX,
      y: e.clientY,
      cx,
      cy,
      lastAngle: angleAt(cx, cy, e.clientX, e.clientY),
      acc: 0,
      moved: false,
    };
    setSnapping(false);
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      /* noop */
    }
  }, []);

  const onPointerMove = useCallback((e) => {
    const d = dragRef.current;
    if (!d) return;
    const a = angleAt(d.cx, d.cy, e.clientX, e.clientY);
    let delta = a - d.lastAngle;
    if (delta > 180) delta -= 360;
    if (delta < -180) delta += 360;
    d.lastAngle = a;
    d.acc += delta;
    d.moved = true;
    const total = selectedRef.current * STEP + d.acc;
    const idx = ((Math.round(total / STEP) % SEGMENTS) + SEGMENTS) % SEGMENTS;
    selectedRef.current = idx;
    setSelected(idx);
    setSpinDeg(total);
  }, []);

  const onPointerUp = useCallback(() => {
    const d = dragRef.current;
    if (!d) return;
    dragRef.current = null;
    dragJustEndedRef.current = d.moved;
    if (d.moved) applySelection(selectedRef.current, true);
  }, [applySelection]);

  const navigateTo = useCallback(
    (to) => {
      if (dragJustEndedRef.current) {
        dragJustEndedRef.current = false;
        return;
      }
      navigate(to);
    },
    [navigate]
  );

  const pressKnob = useCallback(() => {
    navigateTo(DECK_SEGMENTS[selectedRef.current].to);
  }, [navigateTo]);

  const onKeyDown = useCallback(
    (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        step(1);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        step(-1);
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        pressKnob();
      }
    },
    [step, pressKnob]
  );

  // Native wheel listener so rotation of the knob can be prevented cleanly.
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return undefined;
    const onWheel = (e) => {
      e.preventDefault();
      step(e.deltaY > 0 ? 1 : -1);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [step]);

  const seg = DECK_SEGMENTS[selected];

  return (
    <div className="flex w-full flex-col items-center gap-2">
      <DeckLcd selected={selected} compact={compact} />

      <div
        data-testid="central-deck"
        ref={wrapRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onKeyDown={onKeyDown}
        tabIndex={0}
        role="group"
        aria-label={`Terilliom Deck — turn the knob to choose ${seg.label}, press the knob to open it`}
        className="lx-deck relative mx-auto select-none outline-none"
        style={{
          width: size || "372px", // fixed Deck diameter (Terilliom Deck SDK); portrait phones scale it to fit
          aspectRatio: "1 / 1",
          minHeight: compact ? 240 : 300,
        }}
      >
        {/* stage glow */}
        <div className="absolute left-1/2 top-1/2 h-[92%] w-[92%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(30,26,18,0.55),rgba(0,0,0,0.9)_62%)] shadow-[0_0_90px_rgba(255,180,90,0.14),inset_0_0_70px_rgba(0,0,0,0.85)]" />
        <div className="absolute left-1/2 top-1/2 h-[86%] w-[86%] -translate-x-1/2 -translate-y-1/2 rounded-full lx-rainbow-halo" />

        {/* fixed top marker — the option under this marker is the selected mode */}
        <div
          className="pointer-events-none absolute left-1/2 top-0 z-20 -translate-x-1/2"
          aria-hidden="true"
        >
          <div
            className="mx-auto h-0 w-0 border-l-[9px] border-r-[9px] border-t-[12px] border-l-transparent border-r-transparent"
            style={{ borderTopColor: seg.color, filter: `drop-shadow(0 0 6px ${seg.color})` }}
          />
        </div>

        {/* interactive layer — rotates with the knob */}
        <div
          className={`absolute inset-0 ${snapping ? "lx-deck-snap" : ""}`}
          style={{ transform: `rotate(${spinDeg}deg)` }}
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
              <radialGradient id="knobFace" cx="0.5" cy="0.38" r="0.85">
                <stop offset="0" stopColor="#3a3140" />
                <stop offset="0.45" stopColor="#191622" />
                <stop offset="1" stopColor="#08070c" />
              </radialGradient>
              <radialGradient id="knobDot" cx="0.35" cy="0.3" r="1">
                <stop offset="0" stopColor="#fff4e0" />
                <stop offset="1" stopColor="#e08a3c" />
              </radialGradient>
            </defs>

            {/* static plate */}
            <circle cx={C} cy={C} r={OUTER_R} fill="url(#deckPlate)" stroke="url(#deckRimRainbow)" strokeWidth="2.5" />
            <circle cx={C} cy={C} r={SEG_R1 - 6} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />

            {/* static segments — selected one glows, others sit dim */}
            {DECK_SEGMENTS.map((s, i) => {
              const a0 = i * STEP;
              const active = i === selected;
              return (
                <g key={s.id} onClick={() => navigateTo(s.to)} className="deck-seg cursor-pointer"
                  data-testid={`deck-segment-${s.id}`} role="link" aria-label={s.label}>
                  <path
                    d={wedgePath(a0, a0 + STEP)}
                    fill={s.color}
                    fillOpacity={active ? 0.34 : 0.1}
                    stroke={s.color}
                    strokeWidth={active ? 2.4 : 1}
                    strokeOpacity={active ? 1 : 0.4}
                  />
                  {active && (
                    <path
                      d={wedgePath(a0, a0 + STEP)}
                      fill="none"
                      stroke={s.color}
                      strokeWidth="3.5"
                      strokeOpacity="0.75"
                      style={{ filter: `drop-shadow(0 0 6px ${s.color})` }}
                    />
                  )}
                </g>
              );
            })}

            {/* rotating pips ring (CSS spin) */}
            <g className="lx-ring-spin" style={{ transformOrigin: "200px 200px" }}>
              {DECK_SEGMENTS.map((s, i) => {
                const p = polar(C, C, SEG_R1 - 12, i * STEP + STEP / 2);
                return <circle key={s.id} cx={p.x} cy={p.y} r="3.4" fill={s.color} opacity="0.9" />;
              })}
            </g>

            {/* reverse dashed mid ring */}
            <circle className="lx-ring-spin-rev" cx={C} cy={C} r={108} fill="none"
              stroke="rgba(255,255,255,0.22)" strokeWidth="1.2" strokeDasharray="3 7"
              style={{ transformOrigin: "200px 200px" }} />

            {/* drag-group glow arcs */}
            <g transform={`rotate(${spinDeg} 200 200)`}>
              <circle cx={C} cy={C} r={SEG_R2 + 10} fill="none" stroke={seg.color} strokeWidth="1.4" strokeDasharray="1 10" opacity="0.5" />
            </g>

            {/* ---- control knob (the wheel's heart) ---- */}
            <g className="pointer-events-none">
              {/* bezel shadow ring */}
              <circle cx={C} cy={C} r={72} fill="none" stroke="rgba(0,0,0,0.85)" strokeWidth="6" />
              {/* ridge ring — reads as a physical knob */}
              {Array.from({ length: 32 }).map((_, i) => {
                const a = (i * 360) / 32;
                const p0 = polar(C, C, 62, a);
                const p1 = polar(C, C, 70, a);
                return (
                  <line
                    key={i}
                    x1={p0.x}
                    y1={p0.y}
                    x2={p1.x}
                    y2={p1.y}
                    stroke="rgba(255,255,255,0.28)"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                  />
                );
              })}
              {/* knob face */}
              <circle cx={C} cy={C} r={58} fill="url(#knobFace)" stroke={seg.color} strokeWidth="2.5" strokeOpacity="0.85" />
              <circle cx={C} cy={C} r={58} fill="none" stroke="rgba(255,255,255,0.10)" strokeWidth="1" />
              {/* pointer notch — rotates with the wheel */}
              <path
                d={`M ${C - 7} ${C - 56} L ${C + 7} ${C - 56} L ${C} ${C - 42} Z`}
                fill={seg.color}
                style={{ filter: `drop-shadow(0 0 6px ${seg.color})` }}
              />
              {/* grip cross-lines */}
              <circle cx={C} cy={C} r={44} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1.4" />
              <circle cx={C} cy={C} r={32} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
              {/* centre dot (brand light) */}
              <circle cx={C} cy={C} r={12} fill="#0a0910" stroke="url(#deckRimRainbow)" strokeWidth="1.6" />
              <circle cx={C} cy={C} r={4.5} fill="url(#knobDot)" style={{ filter: "drop-shadow(0 0 5px rgba(255,210,140,0.9))" }} />
            </g>
          </svg>

          {/* segment label buttons — the selected mode lights up */}
          {DECK_SEGMENTS.map((s, i) => {
            const mid = i * STEP + STEP / 2;
            const p = polar(C, C, LABEL_R, mid);
            const active = i === selected;
            return (
              <button
                key={s.id}
                data-testid={`deck-label-${s.id}`}
                onClick={() => navigateTo(s.to)}
                className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider transition-all duration-150 lx-deck-touch"
                style={{
                  left: `${(p.x / 400) * 100}%`,
                  top: `${(p.y / 400) * 100}%`,
                  color: active ? "#0b0710" : s.color,
                  borderColor: active ? s.color : "rgba(255,255,255,0.14)",
                  background: active ? s.color : "rgba(6,6,10,0.6)",
                  boxShadow: active ? `0 0 16px ${s.color}, inset 0 0 6px rgba(0,0,0,0.35)` : "none",
                  transform: `translate(-50%, -50%) ${active ? "scale(1.12)" : "scale(1)"}`,
                  zIndex: active ? 5 : 2,
                }}
              >
                {s.label}
              </button>
            );
          })}

          {/* press to open the selected mode */}
          <button
            data-testid="deck-knob"
            onClick={pressKnob}
            className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 cursor-pointer rounded-full lx-deck-touch"
            style={{ width: "34%", height: "34%", background: "transparent", border: "none" }}
            aria-label={`Open ${seg.label}`}
            title={`Open ${seg.label}`}
          />
        </div>

        {/* deck status strip */}
        <div className="pointer-events-none absolute bottom-1 left-1/2 z-30 flex -translate-x-1/2 items-center gap-2 rounded-full border border-white/10 bg-black/55 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-white/55 backdrop-blur">
          <span className="h-1.5 w-1.5 rounded-full bg-[#5ee08a] shadow-[0_0_8px_#5ee08a] lx-pulse-2s" />
          Terilliom Deck · {seg.label}
        </div>
      </div>
    </div>
  );
};

/**
 * Deck — kept for SDK compatibility. The knob + LCD cluster is the real
 * interaction; this renders the same wheel inside a DeckControl.
 */
export const Deck = ({ compact = false, size }) => <DeckControl compact={compact} size={size} />;

export default Deck;
