import React from "react";
import DeckHeader from "./DeckHeader";
import DeckTopNav from "./DeckTopNav";
import DeckSidebar from "./DeckSidebar";
import Deck from "./Deck";
import DeckRightPanel from "./DeckRightPanel";
import DeckDock from "./DeckDock";
import DeckPortrait from "./DeckPortrait";
import AIStatusBanner from "@/components/AIStatusBanner";
import { useDeckMode } from "./DeckScaler";

/**
 * DeckShell — the Terilliom Deck layout, identical across every Terilliom app.
 * Landscape/tablet screens get the full fixed 1280x800 canvas (scaled to fit
 * by DeckScaler). Portrait phones get the same SDK components split across the
 * screen (buttons | wheel | live metrics) and scaled to fit.
 */
export const DeckShell = ({ children }) => {
  const { portrait } = useDeckMode();

  if (portrait) {
    return <DeckPortrait>{children}</DeckPortrait>;
  }

  return (
    <div
      data-testid="deck-shell"
      className="deck-app relative flex h-[800px] w-[1280px] flex-col overflow-hidden bg-[hsl(var(--tp-background))] text-[hsl(var(--tp-text-primary))]"
    >
      <DeckHeader />
      <DeckTopNav />

      <div className="deck-main flex min-h-0 flex-1 gap-4 px-4">
        <DeckSidebar />

        <section className="deck-center flex min-w-0 flex-1 flex-col overflow-hidden">
          <div className="flex shrink-0 items-center justify-center pt-2">
            <Deck compact />
          </div>
          <AIStatusBanner />
          <main className="deck-content min-h-0 flex-1 overflow-y-auto lx-scroll pb-3">{children}</main>
        </section>

        <DeckRightPanel />
      </div>

      <DeckDock />
    </div>
  );
};

export default DeckShell;
