/**
 * Terilliom Deck SDK — Listrix module map.
 * The interface is fixed. Only branding, labels and destinations change.
 */
import {
  Layers, Wallet, Camera, Rocket,
  Plus, Package, Search, Tags,
  Calculator, Percent, Target, Coins,
  ImagePlus, Wand2, Eraser, Stamp,
  Cable, CalendarClock, LayoutTemplate, Radio,
  Inbox, BrainCircuit, Store, Plug, Settings,
} from "lucide-react";

export const RAINBOW = [
  "#ff6a5e", // red
  "#ffb648", // orange
  "#ffe14d", // yellow
  "#5ee08a", // green
  "#3ec8f2", // cyan
  "#9a7bff", // violet
  "#ff6ec7", // magenta
  "#5fd8ff", // sky
];

/** Exactly four primary modules — same buttons, same spacing, same behaviour. */
export const MODULES = [
  { id: "listings", label: "Listings", icon: Layers, to: "/items", match: ["/items"] },
  { id: "pricing", label: "Pricing", icon: Wallet, to: "/financials", match: ["/financials"] },
  { id: "photos", label: "Photos", icon: Camera, to: "/workflows", match: ["/workflows"] },
  { id: "publishing", label: "Publishing", icon: Rocket, to: "/market", match: ["/market", "/integrations"] },
];

/** Exactly four contextual actions per module. */
export const SIDEBAR_ACTIONS = {
  listings: [
    { label: "Add Item", sub: "New product entry", icon: Plus, to: "/workflows" },
    { label: "Inventory", sub: "All items & stock", icon: Package, to: "/items" },
    { label: "Search", sub: "Find anything", icon: Search, to: "/search" },
    { label: "Categories", sub: "Organise shelves", icon: Tags, to: "/settings" },
  ],
  pricing: [
    { label: "Fee Calculator", sub: "Marketplace fees", icon: Calculator, to: "/financials" },
    { label: "Price Rules", sub: "Smart pricing", icon: Percent, to: "/financials" },
    { label: "Profit Targets", sub: "Margin goals", icon: Target, to: "/financials" },
    { label: "Currency", sub: "Multi-currency", icon: Coins, to: "/settings" },
  ],
  photos: [
    { label: "New Batch", sub: "Import photos", icon: ImagePlus, to: "/workflows" },
    { label: "AI Enhance", sub: "Auto improve", icon: Wand2, to: "/ai-manager" },
    { label: "Backgrounds", sub: "Remove & replace", icon: Eraser, to: "/ai-control" },
    { label: "Watermarks", sub: "Protect images", icon: Stamp, to: "/settings" },
  ],
  publishing: [
    { label: "Channels", sub: "Connected stores", icon: Cable, to: "/integrations" },
    { label: "Schedules", sub: "Timed drops", icon: CalendarClock, to: "/market" },
    { label: "Templates", sub: "Listing formats", icon: LayoutTemplate, to: "/settings" },
    { label: "Live Status", sub: "Publish health", icon: Radio, to: "/ai-control" },
  ],
};

/** Exactly six shortcuts in the bottom dock. */
export const DOCK = [
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/ai-manager", label: "AI", icon: BrainCircuit },
  { to: "/market", label: "Market", icon: Store },
  { to: "/integrations", label: "Apps", icon: Plug },
  { to: "/search", label: "Search", icon: Search },
  { to: "/settings", label: "Settings", icon: Settings },
];

export const COMMAND_TO = "/dashboard";

export function getActiveModule(pathname) {
  const hit = MODULES.find((m) => m.match.some((p) => pathname === p || pathname.startsWith(`${p}/`)));
  return hit ? hit.id : "listings";
}

export const DECK_SEGMENTS = [
  { id: "listings", label: "Listings", to: "/items", color: RAINBOW[0] },
  { id: "pricing", label: "Pricing", to: "/financials", color: RAINBOW[1] },
  { id: "photos", label: "Photos", to: "/workflows", color: RAINBOW[2] },
  { id: "publishing", label: "Publishing", to: "/market", color: RAINBOW[3] },
  { id: "ai", label: "AI Studio", to: "/ai-manager", color: RAINBOW[4] },
  { id: "inbox", label: "Inbox", to: "/inbox", color: RAINBOW[5] },
  { id: "apps", label: "Apps", to: "/integrations", color: RAINBOW[6] },
  { id: "command", label: "Command", to: COMMAND_TO, color: RAINBOW[7] },
];

