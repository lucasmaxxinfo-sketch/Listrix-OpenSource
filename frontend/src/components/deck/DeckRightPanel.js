import React from "react";
import { useLocation } from "react-router-dom";
import { Package, Sparkles, Gauge, Cpu } from "lucide-react";
import { useItems, useListings, useAIStatus, useEvents } from "@/lib/queries";
import { getActiveModule } from "./modules";

function MetricCard({ icon: Icon, label, value, hint, color }) {
  return (
    <div className="rounded-2xl border border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))]/70 p-3.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[hsl(var(--tp-text-secondary))]">{label}</span>
        <Icon size={15} style={{ color }} className="drop-shadow-[0_0_6px_currentColor]" />
      </div>
      <p className="mt-1.5 text-2xl font-black tabular-nums text-white" style={{ textShadow: `0 0 18px ${color}66` }}>{value}</p>
      {hint && <p className="mt-0.5 truncate text-[11px] text-[hsl(var(--tp-text-secondary))]">{hint}</p>}
    </div>
  );
}

export const DeckRightPanel = () => {
  const location = useLocation();
  const module = getActiveModule(location.pathname);
  const { data: items = [] } = useItems();
  const { data: listings = [] } = useListings();
  const { data: ai } = useAIStatus();
  const { data: events = [] } = useEvents();
  const aiOk = ai?.reachable === true;
  const live = listings.filter((l) => l.status === "active").length || listings.length;

  return (
    <aside
      data-testid="deck-right-panel"
      className="flex w-[250px] shrink-0 flex-col gap-3 overflow-y-auto py-3 lx-scroll"
      aria-label="Live information"
    >
      <div className="flex items-center justify-between px-1">
        <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-[hsl(var(--tp-text-secondary))]">Live · {module}</p>
        <span className="flex items-center gap-1.5 rounded-full border border-[hsl(var(--tp-border))] bg-black/35 px-2 py-1 text-[10px] font-mono text-[hsl(var(--tp-text-secondary))]">
          <span className={`h-1.5 w-1.5 rounded-full ${aiOk ? "bg-[#5ee08a] shadow-[0_0_8px_#5ee08a]" : "bg-[#ffb648] shadow-[0_0_8px_#ffb648] lx-pulse-2s]"}`} />
          {aiOk ? "AI online" : "AI offline"}
        </span>
      </div>

      <MetricCard icon={Package} label="Inventory" value={items.length} hint="items in stock" color="#ff6a5e" />
      <MetricCard icon={Sparkles} label="Listings" value={live} hint={`${listings.length} total generated`} color="#ffe14d" />
      <MetricCard icon={Gauge} label="Engine" value={aiOk ? "READY" : "STANDBY"} hint={aiOk ? "all systems nominal" : "backend offline"} color="#5ee08a" />

      {/* activity feed */}
      <div className="rounded-2xl border border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))]/70 p-3.5">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[hsl(var(--tp-text-secondary))]">
          <Cpu size={13} className="text-[#3ec8f2]" /> Activity
        </div>
        <div className="mt-2 space-y-2">
          {events.length === 0 && <p className="text-[11px] text-[hsl(var(--tp-text-secondary))]">No recent events yet.</p>}
          {events.slice(0, 4).map((ev) => (
            <div key={ev.id} className="border-l-2 border-[#3ec8f2]/60 pl-2">
              <p className="truncate text-[11px] font-semibold text-[hsl(var(--tp-text-primary))]">{ev.title}</p>
              <p className="truncate text-[10px] text-[hsl(var(--tp-text-secondary))]">{ev.message || ev.type}</p>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

export default DeckRightPanel;
