import { NavLink } from "react-router-dom";
import { LayoutDashboard, Package, Workflow, Store, Cpu, BrainCircuit, Inbox, Plug, Settings, Wallet } from "lucide-react";
import WorkspaceSwitcher from "@/components/WorkspaceSwitcher";
import DeckLogo from "@/components/DeckLogo";
import { useAIStatus } from "@/lib/queries";

const NAV = [
  { to: "/dashboard", label: "Command Center", icon: LayoutDashboard, testid: "nav-dashboard" },
  { to: "/inbox", label: "Inbox", icon: Inbox, testid: "nav-inbox" },
  { to: "/items", label: "Items", icon: Package, testid: "nav-items" },
  { to: "/workflows", label: "Workflows", icon: Workflow, testid: "nav-workflows" },
  { to: "/ai-manager", label: "AI Manager", icon: BrainCircuit, testid: "nav-ai-manager" },
  { to: "/market", label: "Market", icon: Store, testid: "nav-market" },
  { to: "/financials", label: "Financials", icon: Wallet, testid: "nav-financials" },
  { to: "/integrations", label: "Integration Hub", icon: Plug, testid: "nav-integrations" },
  { to: "/ai-control", label: "AI Control", icon: Cpu, testid: "nav-ai-control" },
  { to: "/settings", label: "Settings", icon: Settings, testid: "nav-settings" },
];

export const Sidebar = () => {
  const { data: ai } = useAIStatus();
  const aiOk = ai?.reachable === true;
  return (
  <aside data-testid="app-sidebar" className="hidden md:flex md:flex-col md:w-[260px] shrink-0 border-r border-border bg-card/60 lx-noise">
    <div className="deck-rail flex items-center gap-2.5 px-5 h-16 border-b border-border bg-[linear-gradient(180deg,rgba(255,122,26,0.06),transparent)]">
      <DeckLogo size={34} />
      <div className="leading-tight"><p className="neon-title text-sm font-black tracking-tight">Listrix</p><p className="text-[10px] uppercase tracking-widest text-muted-foreground">Business OS</p></div>
    </div>
    <WorkspaceSwitcher />
    <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto lx-scroll">
      {NAV.map(({ to, label, icon: Icon, testid }) => (
        <NavLink key={to} to={to} data-testid={testid}
          className={({ isActive }) => `group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all ${isActive ? "bg-muted/60 text-foreground shadow-[0_0_14px_rgba(255,122,26,0.22),0_0_0_1px_rgba(255,122,26,0.4)]" : "text-muted-foreground hover:bg-muted/40 hover:text-foreground"}`}>
          {({ isActive }) => (<>{isActive && <span className="absolute left-0 top-2 bottom-2 w-[2px] rounded-full bg-primary" />}<Icon size={18} className="transition-transform group-hover:translate-x-[1px]" /><span className="font-medium">{label}</span></>)}
        </NavLink>
      ))}
    </nav>
    <div className="px-5 py-4 border-t border-border">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className={`h-2 w-2 rounded-full ${aiOk ? "bg-[hsl(var(--lx-green))] shadow-[0_0_8px_hsl(var(--lx-green))]" : "bg-[hsl(var(--lx-orange))] shadow-[0_0_8px_hsl(var(--lx-orange))] animate-lx-glow-pulse]"}`} />
        <span className="font-mono">{aiOk ? "AI engine · online" : "AI engine · offline"}</span>
      </div>
    </div>
  </aside>
  );
};

export default Sidebar;
