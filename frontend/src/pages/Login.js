import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, LogIn, UserPlus } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import DeckLogo from "@/components/DeckLogo";
import DeckStage from "@/components/DeckStage";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, name || undefined);
      toast.success(mode === "login" ? "Signed in" : "Account created");
      navigate("/dashboard");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Request failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="login-page" className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4">
      <div className="pointer-events-none absolute -top-24 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(255,122,26,0.16),transparent_70%)] blur-2xl" />
      <div className="w-full max-w-sm">
        <DeckStage className="mb-7" />
        <div className="deck-rail rounded-2xl border border-border bg-card/70 p-6 shadow-orangeGlow backdrop-blur">
          <div className="mb-6 text-center">
            <DeckLogo size={44} withWordmark className="justify-center" />
            <p className="mt-3 text-sm text-muted-foreground">{mode === "login" ? "Sign in to your business" : "Create your account"}</p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label htmlFor="auth-name" className="mb-1 block text-xs font-medium text-muted-foreground">Business / display name</label>
                <input id="auth-name" value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" placeholder="My Business" />
              </div>
            )}
            <div>
              <label htmlFor="auth-email" className="mb-1 block text-xs font-medium text-muted-foreground">Email</label>
              <input id="auth-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" placeholder="owner@business.com" />
            </div>
            <div>
              <label htmlFor="auth-password" className="mb-1 block text-xs font-medium text-muted-foreground">Password</label>
              <input id="auth-password" type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" placeholder="At least 8 characters" />
            </div>
            <button type="submit" disabled={busy} className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-orangeGlow transition-shadow hover:shadow-orangeGlowStrong disabled:opacity-60">
              {busy ? <Loader2 size={15} className="animate-spin" /> : mode === "login" ? <LogIn size={15} /> : <UserPlus size={15} />}
              {mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <button data-testid="auth-mode-toggle" onClick={() => setMode(mode === "login" ? "register" : "login")} className="mt-4 w-full text-center text-xs text-muted-foreground hover:text-foreground">
            {mode === "login" ? "No account yet? Create one" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}
