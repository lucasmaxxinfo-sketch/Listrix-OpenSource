import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Package, Sparkles, Gauge } from "lucide-react";
import DeckHeader from "./DeckHeader";
import DeckTopNav from "./DeckTopNav";
import Deck from "./Deck";
import DeckDock from "./DeckDock";
import AIStatusBanner from "@/components/AIStatusBanner";
import { SIDEBAR_ACTIONS, getActiveModule } from "./modules";
import { useItems, useListings, useAIStatus } from "@/lib/queries";

/** Wheel diameter on portrait phones — always fits next to the side rails. */
const WHEEL = "min(372px, 54vw, 42vh)";

function MiniMetric({ icon: Icon, label, value, color }) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-0.5 rounded-xl border border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))]/70 px-1 py-2"
      title={label}
    >
      <Icon size={15} style={{ color }} className="drop-shadow-[0_0_6px_currentColor]" />
      <span className="text-sm font-black tabular-nums leading-none text-white" style={{ textShadow: `0 0 12px ${color}66` }}>
        {value}
      </span>
      <span className="text-[8px] font-bold uppercase tracking-wider text-[hsl(var(--tp-text-secondary))]">{label}</span>
    </div>
  );
}

/**
 * DeckPortrait — portrait split of the fixed Terilliom Deck layout.
 * Same SDK components, same behaviour; the fixed 1280x800 tablet canvas is
 * redistributed across the phone screen (buttons | wheel | live metrics)
 * and scaled to fit. Nothing is hidden or redesigned.
 */
export const DeckPortrait = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const module = getActiveModule(location.pathname);
  const actions = SIDEBAR_ACTIONS[module] || SIDEBAR_ACTIONS.listings;
  const { data: items = [] } = useItems();
  const { data: listings = [] } = useListings();
  const { data: ai } = useAIStatus();
  const aiOk = ai?.reachable === true;
  const live = listings.filter((l) => l.status === "active").length || listings.length;

  return (
    <div
      data-testid="deck-portrait"
      className="relative flex h-[100dvh] w-full flex-col overflow-hidden bg-[hsl(var(--tp-background))] text-[hsl(var(--tp-text-primary))]"
    >
      <DeckHeader compact />
      <DeckTopNav compact />

      <div className="deck-portrait-main flex min-h-0 flex-1 flex-col gap-1.5 overflow-hidden px-3 pt-2">
        {/* hero split: buttons | wheel | live metrics */}
        <div className="deck-portrait-hero flex shrink-0 items-center justify-center gap-2" aria-label="Terilliom Deck">
          <div className="flex w-12 shrink-0 flex-col gap-2" aria-label="Contextual actions">
            {actions.map(({ label, icon: Icon, to }, i) => (
              <button
                key={label}
                data-testid={`portrait-action-${i + 1}`}
                onClick={() => navigate(to)}
                className="deck-ico lx-deck-touch relative flex h-12 w-12 items-center justify-center rounded-xl border border-[hsl(var(--tp-border))] text-[#ffb648] transition-all duration-150 hover:border-[#ffb648]/60 hover:shadow-[0_0_16px_rgba(255,182,72,0.35)]"
                aria-label={label}
                title={label}
              >
                <Icon size={19} />
              </button>
            ))}
          </div>

          <div className="flex min-w-0 flex-1 justify-center">
            <Deck compact size={WHEEL} />
          </div>

          <div className="flex w-14 shrink-0 flex-col gap-2" aria-label="Live information">
            <MiniMetric icon={Package} label="Stock" value={items.length} color="#ff6a5e" />
            <MiniMetric icon={Sparkles} label="Live" value={live} color="#ffe14d" />
            <MiniMetric icon={Gauge} label={aiOk ? "AI on" : "AI off"} value={aiOk ? "RDY" : "STBY"} color="#5ee08a" />
          </div>
        </div>

        <AIStatusBanner />

        <main className="deck-content min-h-0 flex-1 overflow-y-auto lx-scroll pb-3">{children}</main>
      </div>

      <DeckDock compact />
    </div>
  );
};

export default DeckPortrait;
