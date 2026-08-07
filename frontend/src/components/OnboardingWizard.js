import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, Lock, Rocket, ShieldCheck, Sparkles, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import DeckLogo from "@/components/DeckLogo";

const REGISTER_FLAG = "listrix:just-registered";

const STEPS = [
  {
    icon: Rocket,
    title: "Welcome to Listrix",
    body: "Listrix turns your inventory into ready-to-publish marketplace listings. This 30-second tour shows you the four things you need to know to get going.",
  },
  {
    icon: Sparkles,
    title: "How it works",
    body: "Add your items, let the AI draft titles, descriptions and prices, approve what you like in the Action Queue, then publish to your marketplaces. Nothing is ever posted without your approval.",
  },
  {
    icon: ShieldCheck,
    title: "Privacy & security",
    body: "Your data stays local by default — passwords are scrambled and marketplace credentials are encrypted. You have already agreed to the terms when you created your account.",
    links: true,
  },
  {
    icon: Lock,
    title: "You're all set",
    body: "Start by adding your first item or checking your dashboard. If you get stuck, the AI assistant in the top bar is ready to help.",
  },
];

export function OnboardingWizard() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    let justRegistered = false;
    try {
      justRegistered = sessionStorage.getItem(REGISTER_FLAG) === "1";
      if (justRegistered) sessionStorage.removeItem(REGISTER_FLAG);
    } catch {}
    if (user && justRegistered) {
      setStep(0);
      setOpen(true);
    }
  }, [user]);

  if (!open) return null;

  const current = STEPS[step];
  const Icon = current.icon;
  const last = step === STEPS.length - 1;

  const close = () => setOpen(false);

  return (
    <div data-testid="onboarding-wizard" className="fixed inset-0 z-[90] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="deck-rail w-full max-w-md rounded-2xl border border-border bg-card/95 p-6 shadow-orangeGlow">
        <div className="mb-5 flex items-center justify-between">
          <DeckLogo size={30} />
          <button type="button" onClick={close} aria-label="Close tour" className="deck-ico flex h-8 w-8 items-center justify-center rounded-full border border-[hsl(var(--tp-border))] text-white/70 transition-colors hover:text-white">
            <X size={15} />
          </button>
        </div>

        <div className="mb-5 flex items-center gap-2">
          {STEPS.map((_, i) => (
            <span key={i} className={`h-1 flex-1 rounded-full transition-colors duration-300 ${i <= step ? "bg-primary shadow-[0_0_8px_var(--primary-glow)]" : "bg-border"}`} />
          ))}
        </div>

        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/15 text-primary shadow-[0_0_18px_-2px_var(--primary-glow)]">
            <Icon size={19} strokeWidth={1.8} />
          </span>
          <div className="min-w-0">
            <h2 className="text-base font-black tracking-tight text-foreground">{current.title}</h2>
            <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">{current.body}</p>
            {current.links && (
              <div className="mt-3 flex flex-wrap gap-2">
                <Link to="/terms" className="rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-primary/50">
                  Terms &amp; Conditions
                </Link>
                <Link to="/privacy" className="rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-primary/50">
                  Privacy Policy
                </Link>
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-semibold text-muted-foreground transition-colors hover:bg-accent disabled:opacity-40"
          >
            <ArrowLeft size={13} /> Back
          </button>
          {last ? (
            <button
              type="button"
              onClick={close}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground shadow-orangeGlow transition-shadow hover:shadow-orangeGlowStrong"
            >
              <Check size={14} /> Get started
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground shadow-orangeGlow transition-shadow hover:shadow-orangeGlowStrong"
            >
              Next <ArrowRight size={13} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default OnboardingWizard;
