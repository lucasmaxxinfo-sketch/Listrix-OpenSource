import React from "react";
import DeckShell from "@/components/deck/DeckShell";

/**
 * AppShell — fixed Terilliom Deck layout.
 * The interface is identical across every Terilliom application;
 * only branding, primary colour, labels and business logic change.
 */
export const AppShell = ({ children }) => <DeckShell>{children}</DeckShell>;

export default AppShell;
