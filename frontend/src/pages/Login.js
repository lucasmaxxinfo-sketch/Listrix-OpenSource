import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, LogIn, UserPlus } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

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
    <div data-testid="login-page" className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm rounded-2xl border border-border bg-card/60 p-6 shadow-orangeGlow">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            {mode === "login" ? <LogIn size={22} /> : <UserPlus size={22} />}
          </div>
          <h1 className="text-xl font-bold tracking-tight">Listrix</h1>
          <p className="text-sm text-muted-foreground">{mode === "login" ? "Sign in to your business" : "Create your account"}</p>
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
  );
}
