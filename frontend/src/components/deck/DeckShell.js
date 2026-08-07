import React from "react";
import DeckHeader from "./DeckHeader";
import DeckTopNav from "./DeckTopNav";
import DeckSidebar from "./DeckSidebar";
import Deck from "./Deck";
import DeckRightPanel from "./DeckRightPanel";
import DeckDock from "./DeckDock";
import AIStatusBanner from "@/components/AIStatusBanner";

export const DeckShell = ({ children }) => (
  <div
    data-testid="deck-shell"
    className="deck-app flex h-[100dvh] w-screen flex-col overflow-hidden bg-[hsl(var(--tp-background))] text-[hsl(var(--tp-text-primary))]"
  >
    <DeckHeader />
    <DeckTopNav />

    <div className="deck-main flex min-h-0 flex-1 gap-3 px-3 md:gap-4 md:px-4">
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

export default DeckShell;
