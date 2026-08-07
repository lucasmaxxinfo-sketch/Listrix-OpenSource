import React, { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useAIStatus } from "@/lib/queries";
import { DOCK } from "./modules";

export const DeckDock = () => {
  const location = useLocation();
  const { data: ai } = useAIStatus();
  const aiOk = ai?.reachable === true;
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <footer
      data-testid="deck-dock"
      className="relative z-20 flex h-[72px] shrink-0 items-center gap-3 border-t border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))]/90 px-5 backdrop-blur"
    >
      <span className="absolute inset-x-0 top-0 h-[2px] lx-rainbow-line opacity-70" aria-hidden="true" />

      {DOCK.map(({ to, label, icon: Icon }) => {
        const active = location.pathname === to;
        return (
          <NavLink
            key={to}
            to={to}
            data-testid={`dock-${label.toLowerCase().replace(/\s+/g, "-")}`}
            className={`lx-deck-touch group relative flex h-[52px] flex-1 max-w-[130px] flex-col items-center justify-center gap-0.5 rounded-xl text-[10px] font-bold uppercase tracking-wide transition-all duration-150 ${
              active ? "text-white" : "text-[hsl(var(--tp-text-secondary))] hover:text-white"
            }`}
          >
            {active && <span className="absolute inset-0 rounded-xl lx-rainbow-bg opacity-20" aria-hidden="true" />}
            <span
              className={`absolute inset-0 rounded-xl border transition-all duration-150 ${
                active
                  ? "border-[#9a7bff]/70 shadow-[0_0_18px_rgba(154,123,255,0.35)]"
                  : "border-transparent group-hover:border-white/20 group-hover:shadow-[0_0_14px_rgba(255,255,255,0.08)]"
              }`}
              aria-hidden="true"
            />
            <Icon size={18} className={`relative transition-transform duration-150 group-hover:scale-110 ${active ? "drop-shadow-[0_0_7px_rgba(154,123,255,0.9)]" : ""}`} />
            <span className="relative">{label}</span>
          </NavLink>
        );
      })}

      {/* status + clock */}
      <div className="ml-auto flex shrink-0 items-center gap-3 pl-2">
        <div className="flex items-center gap-2 rounded-full border border-[hsl(var(--tp-border))] bg-black/35 px-3 py-1.5">
          <span className={`h-2 w-2 rounded-full ${aiOk ? "bg-[#5ee08a] shadow-[0_0_8px_#5ee08a]" : "bg-[#ffb648] shadow-[0_0_8px_#ffb648] lx-pulse-2s"}`} />
          <span className="font-mono text-[10px] uppercase tracking-wider text-[hsl(var(--tp-text-secondary))]">{aiOk ? "AI online" : "AI offline"}</span>
        </div>
        <div className="rounded-full border border-[hsl(var(--tp-border))] bg-black/35 px-3 py-1.5 font-mono text-xs tabular-nums text-[hsl(var(--tp-text-primary))]">
          {now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
        </div>
      </div>
    </footer>
  );
};

export default DeckDock;
