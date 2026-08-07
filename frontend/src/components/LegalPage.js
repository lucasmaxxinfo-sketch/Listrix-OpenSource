import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import DeckLogo from "@/components/DeckLogo";

export default function LegalPage({ title, updated, children }) {
  return (
    <div className="relative min-h-screen overflow-y-auto bg-background px-4 py-10 text-foreground">
      <div className="pointer-events-none absolute -top-24 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(255,122,26,0.14),transparent_70%)] blur-2xl" />
      <div className="relative mx-auto w-full max-w-2xl">
        <Link to="/login" className="mb-6 inline-flex items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground">
          <ArrowLeft size={14} /> Back to sign in
        </Link>

        <div className="deck-rail rounded-2xl border border-border bg-card/70 p-6 shadow-orangeGlow backdrop-blur md:p-8">
          <div className="mb-6 flex items-center gap-3 border-b border-border pb-5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-primary shadow-[0_0_18px_-2px_var(--primary-glow)]">
              <ShieldCheck size={20} strokeWidth={1.8} />
            </span>
            <div>
              <h1 className="text-lg font-black tracking-tight">{title}</h1>
              <p className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">Last updated: {updated}</p>
            </div>
          </div>
          <div className="space-y-5 text-sm leading-relaxed text-muted-foreground">{children}</div>

          <div className="mt-8 flex items-center justify-between gap-3 border-t border-border pt-5">
            <DeckLogo size={26} />
            <Link to="/login" className="rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground shadow-orangeGlow transition-shadow hover:shadow-orangeGlowStrong">
              Back to sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
