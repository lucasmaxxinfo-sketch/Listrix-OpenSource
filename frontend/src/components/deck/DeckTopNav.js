import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { MODULES, getActiveModule } from "./modules";

export const DeckTopNav = () => {
  const location = useLocation();
  const activeModule = getActiveModule(location.pathname);

  return (
    <nav
      data-testid="deck-topnav"
      className="flex h-[76px] shrink-0 items-stretch justify-center gap-2 border-b border-[hsl(var(--tp-border))] bg-[hsl(var(--tp-panel))]/60 px-3 md:gap-4"
      aria-label="Primary modules"
    >
      {MODULES.map(({ id, label, icon: Icon, to }) => {
        const active = activeModule === id;
        return (
          <NavLink
            key={id}
            to={to}
            data-testid={`nav-${id}`}
            className={`lx-deck-touch group relative flex min-w-[110px] flex-1 max-w-[220px] items-center justify-center gap-2.5 rounded-2xl px-4 text-sm font-bold uppercase tracking-wide transition-all duration-150 ${
              active
                ? "text-white"
                : "text-[hsl(var(--tp-text-secondary))] hover:text-white"
            }`}
          >
            {active && (
              <span className="absolute inset-0 rounded-2xl lx-rainbow-bg opacity-25 transition-opacity duration-150" aria-hidden="true" />
            )}
            <span
              className={`absolute inset-0 rounded-2xl border transition-all duration-150 ${
                active
                  ? "border-[#ffb648]/70 shadow-[0_0_24px_rgba(255,182,72,0.35),inset_0_0_18px_rgba(255,182,72,0.12)]"
                  : "border-[hsl(var(--tp-border))] group-hover:border-white/25 group-hover:shadow-[0_0_16px_rgba(255,255,255,0.08)]"
              }`}
              aria-hidden="true"
            />
            <Icon size={19} className={`relative transition-transform duration-150 group-hover:scale-110 ${active ? "drop-shadow-[0_0_8px_rgba(255,182,72,0.9)]" : ""}`} />
            <span className="relative">{label}</span>
            <span
              className={`absolute bottom-1 left-1/2 h-[3px] w-8 -translate-x-1/2 rounded-full transition-all duration-150 ${
                active ? "lx-rainbow-line opacity-100" : "opacity-0 group-hover:opacity-40"
              }`}
              aria-hidden="true"
            />
          </NavLink>
        );
      })}
    </nav>
  );
};

export default DeckTopNav;
