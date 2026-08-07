import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell, CheckCheck, Search, Settings, Sparkles, LogOut, LogIn, Plus, ChevronDown,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import DeckLogo from "@/components/DeckLogo";
import { useNotifications, useMarkAllNotificationsRead } from "@/lib/queries";

export const DeckHeader = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [q, setQ] = useState("");
  const [notifOpen, setNotifOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const { data: unread = [] } = useNotifications(true);
  const markRead = useMarkAllNotificationsRead();

  const submitSearch = (e) => {
    e.preventDefault();
    if (q.trim().length < 2) return;
    navigate(`/search?q=${encodeURIComponent(q.trim())}`);
    setQ("");
  };

  const openAssistant = () => {
    window.dispatchEvent(new CustomEvent("listrix:open-assistant"));
  };

  const initials = (user?.name || user?.email || "U")
    .split(/[\s@._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join("") || "U";

  return (
    <header
      data-testid="deck-header"
      className="relative z-30 flex h-16 shrink-0 items-center justify-between gap-3 border-b border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))]/90 px-5 backdrop-blur"
    >
      {/* rainbow rail */}
      <span className="absolute inset-x-0 top-0 h-[2px] lx-rainbow-line" aria-hidden="true" />

      {/* left: logo + app name */}
      <div className="flex min-w-0 items-center gap-2.5">
        <button onClick={() => navigate("/dashboard")} className="flex items-center gap-2.5 lx-deck-touch" data-testid="header-logo">
          <DeckLogo size={34} rainbow />
          <span className="leading-tight">
            <span className="block text-base font-black tracking-tight text-white lx-neon">Listrix</span>
            <span className="block text-[9px] uppercase tracking-[0.3em] text-[hsl(var(--tp-text-secondary))]">Terilliom Deck</span>
          </span>
        </button>
      </div>

      {/* center: search */}
      <form onSubmit={submitSearch} className="min-w-0 flex-1 max-w-md" data-testid="global-search">
        <div className="relative">
          <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[hsl(var(--tp-text-secondary))]" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search items, events, inbox…"
            className="h-11 w-full rounded-xl border border-[hsl(var(--tp-border))] bg-black/40 py-2 pl-9 pr-3 text-sm text-[hsl(var(--tp-text-primary))] outline-none transition-all duration-150 placeholder:text-[hsl(var(--tp-text-secondary))]/70 focus:border-[#ffb648]/60 focus:shadow-[0_0_18px_rgba(255,182,72,0.18)]"
          />
        </div>
      </form>

      {/* right: actions */}
      <div className="flex items-center gap-1.5 md:gap-2">
        <button
          data-testid="assistant-header-button"
          onClick={openAssistant}
          className="deck-ico lx-deck-touch relative inline-flex h-11 items-center gap-2 rounded-xl border border-[hsl(var(--tp-border))] bg-black/35 px-3 text-sm font-semibold text-[hsl(var(--tp-text-primary))] transition-all duration-150 hover:border-[#9a7bff]/70 hover:shadow-[0_0_18px_rgba(154,123,255,0.3)]"
          aria-label="AI Assistant"
        >
          <Sparkles size={17} className="text-[#9a7bff]" />
          <span className="inline">AI Assistant</span>
        </button>

        <div className="relative" data-testid="notifications-bell">
          <button
            onClick={() => { setNotifOpen((v) => !v); setUserOpen(false); }}
            className="deck-ico lx-deck-touch relative flex h-11 w-11 items-center justify-center rounded-xl border border-[hsl(var(--tp-border))] bg-black/35 text-[hsl(var(--tp-text-primary))] transition-all duration-150 hover:border-[#3ec8f2]/70 hover:shadow-[0_0_18px_rgba(62,200,242,0.28)]"
            aria-label="Notifications"
          >
            <Bell size={18} />
            {unread.length > 0 && (
              <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-[#ff6a5e] px-1 text-[10px] font-bold text-black shadow-[0_0_10px_rgba(255,106,94,0.8)]">
                {unread.length}
              </span>
            )}
          </button>
          {notifOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setNotifOpen(false)} />
              <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-2xl border border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))] shadow-[0_18px_50px_rgba(0,0,0,0.6)]">
                <div className="flex items-center justify-between border-b border-[hsl(var(--tp-border))] px-4 py-3">
                  <p className="text-sm font-bold text-white">Notifications</p>
                  {unread.length > 0 && (
                    <button data-testid="mark-notifications-read" onClick={() => markRead.mutate()} className="inline-flex items-center gap-1 text-[11px] text-[#3ec8f2] hover:underline">
                      <CheckCheck size={12} /> Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-80 overflow-y-auto lx-scroll">
                  {unread.length === 0 ? (
                    <p className="px-4 py-10 text-center text-xs text-[hsl(var(--tp-text-secondary))]">You're all caught up.</p>
                  ) : (
                    unread.slice(0, 10).map((n) => (
                      <button key={n.id} onClick={() => { setNotifOpen(false); if (n.link) navigate(n.link); }}
                        className="block w-full border-b border-[hsl(var(--tp-border))]/50 px-4 py-3 text-left transition-colors duration-150 hover:bg-white/[0.04]">
                        <p className="text-xs font-semibold text-[hsl(var(--tp-text-primary))]">{n.title}</p>
                        {n.body && <p className="mt-0.5 line-clamp-2 text-[11px] text-[hsl(var(--tp-text-secondary))]">{n.body}</p>}
                      </button>
                    ))
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        <button
          data-testid="header-new-item"
          onClick={() => navigate("/workflows")}
          className="deck-ico lx-deck-touch inline-flex h-11 items-center gap-2 rounded-xl bg-[#ffb648] px-4 text-sm font-bold text-black transition-all duration-150 hover:brightness-110"
        >
          <Plus size={17} /> New Item
        </button>

        <div className="relative">
          {user ? (
            <>
              <button
                onClick={() => { setUserOpen((v) => !v); setNotifOpen(false); }}
                data-testid="header-user-menu"
                className="deck-ico lx-deck-touch flex h-11 items-center gap-2 rounded-xl border border-[hsl(var(--tp-border))] bg-black/35 px-2 text-[hsl(var(--tp-text-primary))] transition-all duration-150 hover:border-[#5ee08a]/70 hover:shadow-[0_0_18px_rgba(94,224,138,0.22)]"
                aria-label="User menu"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#5ee08a]/20 text-xs font-black text-[#5ee08a]">{initials}</span>
                <span className="block max-w-[140px] truncate text-xs text-[hsl(var(--tp-text-secondary))]">{user.name || user.email}</span>
                <ChevronDown size={14} className="text-[hsl(var(--tp-text-secondary))]" />
              </button>
              {userOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setUserOpen(false)} />
                  <div className="absolute right-0 z-50 mt-2 w-64 overflow-hidden rounded-2xl border border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))] p-2 shadow-[0_18px_50px_rgba(0,0,0,0.6)]">
                    <div className="border-b border-[hsl(var(--tp-border))] px-3 py-2.5">
                      <p className="truncate text-sm font-bold text-white">{user.name || "Listrix User"}</p>
                      <p className="truncate text-[11px] text-[hsl(var(--tp-text-secondary))]">{user.email}</p>
                    </div>
                    <button onClick={() => { setUserOpen(false); navigate("/settings"); }} className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-[hsl(var(--tp-text-primary))] transition-colors duration-150 hover:bg-white/[0.06]">
                      <Settings size={15} /> Settings
                    </button>
                    <button data-testid="header-signout" onClick={logout} className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-[#ff6a5e] transition-colors duration-150 hover:bg-[#ff6a5e]/10">
                      <LogOut size={15} /> Sign out
                    </button>
                  </div>
                </>
              )}
            </>
          ) : (
            <button data-testid="header-signin" onClick={() => navigate("/login")} className="deck-ico lx-deck-touch flex h-11 items-center gap-2 rounded-xl border border-[hsl(var(--tp-border))] bg-black/35 px-3 text-sm font-semibold text-[hsl(var(--tp-text-primary))] transition-all duration-150 hover:border-[#3ec8f2]/70 hover:shadow-[0_0_18px_rgba(62,200,242,0.25)]">
              <LogIn size={16} /> <span className="inline">Sign in</span>
            </button>
          )}
        </div>

        <button
          onClick={() => navigate("/settings")}
          className="deck-ico lx-deck-touch flex h-11 w-11 items-center justify-center rounded-xl border border-[hsl(var(--tp-border))] bg-black/35 text-[hsl(var(--tp-text-primary))] transition-all duration-150 hover:border-[#ff6ec7]/70 hover:shadow-[0_0_18px_rgba(255,110,199,0.25)]"
          aria-label="Settings"
        >
          <Settings size={18} />
        </button>
      </div>
    </header>
  );
};

export default DeckHeader;
