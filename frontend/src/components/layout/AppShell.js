import { useState } from "react";
import { LogIn, LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useLocation, useNavigate, NavLink } from "react-router-dom";
import { Menu, X, Plus, Sparkles, LayoutDashboard, Package, Workflow, Store, Cpu, Bell, Wallet, Search, CheckCheck } from "lucide-react";
import Sidebar from "@/components/layout/Sidebar";
import DeckLogo from "@/components/DeckLogo";
import AIStatusBanner from "@/components/AIStatusBanner";
import { useNotifications, useMarkAllNotificationsRead } from "@/lib/queries";

const TITLES = {
  "/dashboard": { title: "Command Center", sub: "Real-time resale operations overview" },
  "/inbox": { title: "Inbox", sub: "Business operations inbox" },
  "/items": { title: "Items", sub: "Your inventory" },
  "/workflows": { title: "Workflows", sub: "Create item \u2192 AI vision \u2192 listing" },
  "/ai-manager": { title: "AI Manager", sub: "Action queue & marketing intelligence" },
  "/market": { title: "Market", sub: "AI-generated listings" },
  "/financials": { title: "Financials", sub: "Fees, tax & potential profit" },
  "/integrations": { title: "Integration Hub", sub: "External marketplace connectors" },
  "/ai-control": { title: "AI Control", sub: "Model status & activity" },
};

const MOBILE_NAV = [
  { to: "/dashboard", label: "Command Center", icon: LayoutDashboard },
  { to: "/inbox", label: "Inbox", icon: Package },
  { to: "/items", label: "Items", icon: Package },
  { to: "/workflows", label: "Workflows", icon: Workflow },
  { to: "/ai-manager", label: "AI Manager", icon: Cpu },
  { to: "/market", label: "Market", icon: Store },
  { to: "/financials", label: "Financials", icon: Wallet },
  { to: "/integrations", label: "Integration Hub", icon: Store },
  { to: "/ai-control", label: "AI Control", icon: Cpu },
];

export const AppShell = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [q, setQ] = useState("");
  const { data: unread = [] } = useNotifications(true);
  const markRead = useMarkAllNotificationsRead();
  const meta = TITLES[location.pathname] || { title: "Listrix", sub: "" };

  const submitSearch = (e) => {
    e.preventDefault();
    if (q.trim().length < 2) return;
    navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 h-full w-[260px] bg-card border-r border-border p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <DeckLogo size={28} />
                <span className="font-black tracking-tight">Listrix</span>
              </div>
              <button onClick={() => setMobileOpen(false)} className="text-muted-foreground"><X size={20} /></button>
            </div>
            <nav className="space-y-1">
              {MOBILE_NAV.map(({ to, label, icon: Icon }) => (
                <NavLink key={to} to={to} onClick={() => setMobileOpen(false)} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${isActive ? "bg-muted/60 text-foreground" : "text-muted-foreground"}`}>
                  <Icon size={18} /> {label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        {/* Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-border bg-background/85 backdrop-blur px-4 md:px-6">
          <div className="flex items-center gap-3 min-w-0">
            <button className="md:hidden text-muted-foreground" onClick={() => setMobileOpen(true)} data-testid="mobile-menu-button">
              <Menu size={22} />
            </button>
            <div className="min-w-0">
              <h1 className="neon-title text-lg font-semibold tracking-tight truncate">{meta.title}</h1>
              <p className="text-xs text-muted-foreground truncate">{meta.sub}</p>
            </div>
            <div className="eq hidden sm:flex" aria-hidden="true"><span /><span /><span /><span /><span /><span /></div>
            <form onSubmit={submitSearch} className="ml-3 hidden lg:block" data-testid="global-search">
              <div className="relative">
                <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search items, events, inbox…" className="w-56 rounded-lg border border-border bg-muted/30 py-1.5 pl-8 pr-3 text-xs outline-none transition-colors focus:border-primary/50 focus:w-72" />
              </div>
            </form>
          </div>
          <div className="flex items-center gap-2">
            {user ? (
              <div className="flex items-center gap-2 rounded-lg border border-border bg-secondary px-2.5 py-1.5">
                <span className="hidden max-w-[160px] truncate text-xs text-muted-foreground lg:block" title={user.email}>{user.email}</span>
                <button data-testid="header-signout" onClick={logout} className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground" aria-label="Sign out">
                  <LogOut size={13} /> <span className="hidden sm:inline">Sign out</span>
                </button>
              </div>
            ) : (
              <button data-testid="header-signin" onClick={() => navigate("/login")} className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-2 text-sm font-semibold text-secondary-foreground transition-colors hover:bg-muted/50">
                <LogIn size={15} /> <span className="hidden sm:inline">Sign in</span>
              </button>
            )}
            <div className="relative" data-testid="notifications-bell">
              <button
                onClick={() => setNotifOpen((v) => !v)}
                className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-secondary text-muted-foreground transition-colors hover:text-foreground"
                aria-label="Notifications"
              >
                <Bell size={16} />
                {unread.length > 0 && <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground shadow-[0_0_6px_hsl(var(--lx-orange))]">{unread.length}</span>}
              </button>
              {notifOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setNotifOpen(false)} />
                  <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-border bg-card shadow-panelSoft">
                    <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
                      <p className="text-sm font-semibold">Notifications</p>
                      {unread.length > 0 && (
                        <button data-testid="mark-notifications-read" onClick={() => { markRead.mutate(); }} className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline"><CheckCheck size={12} /> Mark all read</button>
                      )}
                    </div>
                    <div className="max-h-80 overflow-y-auto">
                      {unread.length === 0 ? <p className="px-4 py-8 text-center text-xs text-muted-foreground">You're all caught up.</p> : unread.slice(0, 10).map((n) => (
                        <button key={n.id} onClick={() => { setNotifOpen(false); if (n.link) navigate(n.link); }} className="block w-full border-b border-border/50 px-4 py-2.5 text-left transition-colors hover:bg-muted/30">
                          <p className="text-xs font-semibold">{n.title}</p>
                          {n.body && <p className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground">{n.body}</p>}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
            <button
              data-testid="header-new-item"
              onClick={() => navigate("/workflows")}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlowStrong transition-shadow hover:shadow-orangeGlow active:scale-[0.98]"
            >
              <Plus size={16} /> <span className="hidden sm:inline">New Item</span>
            </button>
            <button
              data-testid="header-generate"
              onClick={() => navigate("/workflows")}
              className="inline-flex items-center gap-2 rounded-lg border border-border bg-secondary px-3.5 py-2 text-sm font-semibold text-secondary-foreground transition-colors hover:bg-muted/50"
            >
              <Sparkles size={16} /> <span className="hidden sm:inline">Generate</span>
            </button>
          </div>
        </header>

        <AIStatusBanner />
        <main className="flex-1 p-4 md:p-6 lx-scroll overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
};

export default AppShell;
