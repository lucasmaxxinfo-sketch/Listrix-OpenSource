import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAIStatus } from "@/lib/queries";
import { SIDEBAR_ACTIONS, getActiveModule } from "./modules";

export const DeckSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const activeModule = getActiveModule(location.pathname);
  const actions = SIDEBAR_ACTIONS[activeModule] || SIDEBAR_ACTIONS.listings;
  const { data: ai } = useAIStatus();
  const aiOk = ai?.reachable === true;

  return (
    <aside
      data-testid="app-sidebar"
      className="flex w-[240px] shrink-0 flex-col gap-3 overflow-y-auto py-3 lx-scroll"
      aria-label="Contextual actions"
    >
      <p className="px-2 text-[10px] font-bold uppercase tracking-[0.24em] text-[hsl(var(--tp-text-secondary))]">
        {activeModule} · Actions
      </p>
      {actions.map(({ label, sub, icon: Icon, to }, i) => (
        <button
          key={label}
          data-testid={`sidebar-action-${i + 1}`}
          onClick={() => navigate(to)}
          className="lx-deck-touch group relative flex items-center gap-3 overflow-hidden rounded-2xl border border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))]/70 p-3 text-left transition-all duration-150 hover:-translate-y-0.5 hover:border-[#ffb648]/60 hover:shadow-[0_0_20px_rgba(255,182,72,0.16)]"
        >
          <span className="absolute left-0 top-0 h-full w-[3px] lx-rainbow-line opacity-40 transition-opacity duration-150 group-hover:opacity-100" aria-hidden="true" />
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-[hsl(var(--tp-border))] bg-black/40 text-[#ffb648] transition-all duration-150 group-hover:shadow-[0_0_14px_rgba(255,182,72,0.4)]">
            <Icon size={20} />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-bold text-[hsl(var(--tp-text-primary))]">{label}</span>
            <span className="block truncate text-[11px] text-[hsl(var(--tp-text-secondary))]">{sub}</span>
          </span>
        </button>
      ))}

      {/* AI engine status footer */}
      <div className="mt-auto rounded-2xl border border-[hsl(var(--tp-border))] bg-black/30 p-3">
        <div className="flex items-center gap-2 text-[11px] text-[hsl(var(--tp-text-secondary))]">
          <span className={`h-2 w-2 rounded-full ${aiOk ? "bg-[#5ee08a] shadow-[0_0_8px_#5ee08a]" : "bg-[#ffb648] shadow-[0_0_8px_#ffb648] lx-pulse-2s"}`} />
          <span className="font-mono">{aiOk ? "AI engine · online" : "AI engine · offline"}</span>
        </div>
      </div>
    </aside>
  );
};

export default DeckSidebar;
