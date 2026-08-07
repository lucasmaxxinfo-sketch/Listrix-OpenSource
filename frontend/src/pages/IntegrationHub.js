import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import {
  Loader2, Plug, RefreshCw, Store, Mail, LineChart, Users, Check, X,
  ExternalLink, KeyRound, ShieldCheck, AlertTriangle, Lock, Boxes,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatTime } from "@/lib/derive";

const KIND_ICON = { marketplace: Store, communication: Mail, data: LineChart };
const PLATFORM_ICON = { "Stocksix": Boxes, "TradeMe": Store, "Facebook Marketplace": Store, "Gmail": Mail, "Pricing Signals": LineChart, "Competitor Listings": Users };

// Platforms with a real live adapter get the full wizard; the rest keep the legacy toggle.
const WIZARD_PLATFORMS = new Set(["Stocksix", "TradeMe", "Facebook Marketplace", "Gmail"]);

const FIELD_LABELS = {
  base_url: "Stocksix address (URL)",
  api_key: "API Key",
  consumer_key: "Consumer Key",
  consumer_secret: "Consumer Secret",
  callback_url: "Callback URL",
  page_token: "Page Access Token",
  page_id: "Page ID (optional)",
  access_token: "Gmail Access Token",
};

const GUIDE = {
  "Stocksix": {
    link: "https://github.com/lucasmaxxinfo-sketch/stocksix",
    linkLabel: "Stocksix (your inventory hub — open source)",
    steps: [
      "Start the Stocksix app on this computer and open Settings → Integrations.",
      "Create an API key (copy it) — it lets Listrix read your inventory.",
      "Paste the key below, and set the address to where Stocksix is running (usually http://localhost:3000).",
    ],
  },
  "TradeMe": {
    link: "https://developer.trademe.co.nz",
    linkLabel: "trade.me/developer — free account",
    steps: [
      "Create a free TradeMe developer account and register an app.",
      "Copy the Consumer Key and Consumer Secret it gives you.",
      "Set the app's Callback URL to your hosted Listrix address (the builder will confirm the exact link).",
    ],
  },
  "Facebook Marketplace": {
    link: "https://developers.facebook.com",
    linkLabel: "developers.facebook.com — free account",
    steps: [
      "Create a Facebook App for your business page (free).",
      "Get a Page Access Token for your Marketplace page.",
      "Paste the token below. Optionally add the Page ID to target one specific page.",
    ],
  },
  "Gmail": {
    link: "https://console.cloud.google.com",
    linkLabel: "console.cloud.google.com — free account",
    steps: [
      "Create a Google Cloud project and turn on the Gmail API.",
      "Generate an access token with Gmail read-only access.",
      "Paste it below — Listrix only reads buyer messages; it never sends.",
    ],
  },
};

function statusBadge(c) {
  if (c.auth_status === "connected" && c.mode === "live") {
    return { label: "Connected · live", cls: "border-[rgba(34,197,94,0.3)] bg-[rgba(34,197,94,0.12)] text-[hsl(var(--lx-green))]", dot: "bg-[hsl(var(--lx-green))]" };
  }
  if (c.auth_status === "connected") {
    return { label: "Connected · simulated", cls: "border-[rgba(251,191,36,0.3)] bg-[rgba(251,191,36,0.12)] text-amber-400", dot: "bg-amber-400" };
  }
  if (c.configured) {
    return { label: "Configured · live", cls: "border-[rgba(59,130,246,0.35)] bg-[rgba(59,130,246,0.12)] text-blue-400", dot: "bg-blue-400" };
  }
  if (c.mode === "offline") {
    return { label: "Backend offline", cls: "border-red-500/30 bg-red-500/10 text-red-400", dot: "bg-red-400" };
  }
  return { label: "Disconnected", cls: "border-border bg-muted/40 text-muted-foreground", dot: "bg-muted-foreground" };
}

export default function IntegrationHub() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);
  const [wizard, setWizard] = useState(null); // platform name or null
  const [fields, setFields] = useState({});
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const FALLBACK_ROWS = [
    { platform: "Stocksix", kind: "inventory", auth_status: "disconnected", permissions: ["read_inventory", "sync_items"], sync_enabled: false, mode: "offline", note: "Backend offline — start Listrix on your computer to connect." },
    { platform: "TradeMe", kind: "marketplace", auth_status: "disconnected", permissions: ["read_listings", "create_listing_draft"], sync_enabled: false, mode: "offline" },
    { platform: "Facebook Marketplace", kind: "marketplace", auth_status: "disconnected", permissions: ["read_listings"], sync_enabled: false, mode: "offline" },
    { platform: "Gmail", kind: "communication", auth_status: "disconnected", permissions: ["read_messages"], sync_enabled: false, mode: "offline" },
    { platform: "Pricing Signals", kind: "data", auth_status: "disconnected", permissions: ["read_market_prices"], sync_enabled: false, mode: "offline" },
    { platform: "Competitor Listings", kind: "data", auth_status: "disconnected", permissions: ["read_competitors"], sync_enabled: false, mode: "offline" },
  ];

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/integrations/status");
      setRows(Array.isArray(data) && data.length ? data : FALLBACK_ROWS);
    } catch {
      setRows(FALLBACK_ROWS);
      toast.error("Backend offline — showing the connection wizard in demo mode. Start Listrix on your computer to connect for real.");
    } finally { setLoading(false); }
  }, []);

  // TradeMe OAuth callback: the provider redirects back with oauth_token + oauth_verifier.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("oauth_token");
    const verifier = params.get("oauth_verifier");
    if (token && verifier) {
      api.post("/integrations/TradeMe/oauth/callback", { oauth_token: token, oauth_verifier: verifier })
        .then(() => { toast.success("TradeMe connected"); window.history.replaceState({}, "", "/integrations"); load(); })
        .catch((e) => toast.error(e?.response?.data?.detail || "OAuth callback failed"));
    }
  }, [load]);
  useEffect(() => { load(); }, [load]);

  const openWizard = (p) => { setWizard(p); setFields({}); setTestResult(null); };
  const closeWizard = () => { setWizard(null); setFields({}); setTestResult(null); setTesting(false); setSaving(false); };

  const runTest = async () => {
    if (!wizard) return;
    setTesting(true); setTestResult(null);
    try {
      const { data } = await api.post(`/integrations/${encodeURIComponent(wizard)}/test`);
      setTestResult(data);
      if (data?.ok) toast.success("Connection test passed"); else toast.error("Connection test failed");
    } catch (e) { setTestResult({ ok: false, message: e?.response?.data?.detail || "Test could not be run" }); }
    finally { setTesting(false); }
  };

  const saveAndConnect = async () => {
    if (!wizard) return;
    setSaving(true);
    try {
      const credentials = Object.fromEntries(Object.entries(fields).filter(([, v]) => String(v || "").trim() !== ""));
      if (Object.keys(credentials).length === 0) { toast.error("Paste at least one credential value first"); setSaving(false); return; }
      await api.post(`/integrations/${encodeURIComponent(wizard)}/config`, { credentials });
      const { data } = await api.post(`/integrations/${encodeURIComponent(wizard)}/connect`);
      if (data?.authorize_url) {
        window.open(data.authorize_url, "_blank", "noopener");
        toast.info("Authorize TradeMe in the new tab — you'll return here when done.");
      } else {
        toast.success(`${wizard} is connected`);
      }
      await load();
      closeWizard();
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not save the connection"); }
    finally { setSaving(false); }
  };

  const disconnect = async (p) => {
    setBusy(p);
    try {
      await api.post(`/integrations/${encodeURIComponent(p)}/disconnect`);
      toast.success(`${p} disconnected`);
      await load();
      if (wizard === p) closeWizard();
    } catch (e) { toast.error(e?.response?.data?.detail || "Disconnect failed"); } finally { setBusy(null); }
  };

  const legacyConnect = async (p) => {
    setBusy(p);
    try {
      const { data } = await api.post(`/integrations/${encodeURIComponent(p)}/connect`);
      await load();
      toast.success(data?.auth_status === "connected" ? `${p} connected` : `${p} disconnected`);
    } catch { toast.error("Action failed"); } finally { setBusy(null); }
  };

  const sync = async (p) => {
    setBusy(p);
    try {
      const { data } = await api.post(`/integrations/${encodeURIComponent(p)}/sync`);
      await load();
      toast.success(data.note || "Synced");
    } catch (e) { toast.error(e?.response?.data?.detail || "Sync failed"); } finally { setBusy(null); }
  };

  const wizRow = wizard ? rows.find((r) => r.platform === wizard) : null;
  const wizGuide = wizard ? GUIDE[wizard] : null;

  return (
    <div data-testid="integration-hub-page">
      <div className="mb-5 rounded-xl border border-primary/20 bg-card/50 p-4 text-sm text-muted-foreground shadow-orangeGlow">
        <span className="font-semibold text-foreground">Approval-gated connector layer.</span> No auto-posting or auto-messaging — every external action needs your approval and is logged. Use the <span className="text-foreground">wizard</span> to paste your own TradeMe / Facebook / Gmail credentials (encrypted, stored per business). Without credentials, connectors run on simulated data.
      </div>

      {loading ? <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div> : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((c) => {
            const Icon = PLATFORM_ICON[c.platform] || KIND_ICON[c.kind] || Plug;
            const badge = statusBadge(c);
            const connected = c.auth_status === "connected";
            const isWizard = WIZARD_PLATFORMS.has(c.platform);
            return (
              <div key={c.platform} data-testid="connector-card" className="panel-3d flex flex-col rounded-xl p-5">
                <div className="flex items-center justify-between">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted/40 text-foreground"><Icon size={20} /></span>
                  <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-semibold ${badge.cls}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${badge.dot}`} /> {badge.label}
                  </span>
                </div>
                <h3 className="mt-3 font-semibold">{c.platform}</h3>
                <p className="text-xs capitalize text-muted-foreground">{c.kind}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">{(c.permissions || []).map((p) => <span key={p} className="rounded-full bg-muted/40 px-2 py-0.5 text-[11px] text-muted-foreground">{p}</span>)}</div>
                {c.last_test && c.last_test.ok === false && (
                  <p className="mt-2 flex items-start gap-1 text-[11px] text-red-400"><AlertTriangle size={12} className="mt-0.5 shrink-0" /> Last test failed: {c.last_test.message}</p>
                )}
                <p className="mt-2 text-[11px] text-muted-foreground">
                  Last sync: {c.last_sync ? formatTime(c.last_sync) : "never"} {c.mode === "live" ? "· live" : "· simulated"}
                </p>
                <div className="mt-4 flex gap-2">
                  {isWizard ? (
                    <button data-testid="connector-connect-button" onClick={() => openWizard(c.platform)} disabled={busy === c.platform} className={`inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold disabled:opacity-60 ${connected || c.configured ? "border border-border bg-secondary text-secondary-foreground hover:bg-muted/50" : "bg-primary text-primary-foreground shadow-orangeGlow"}`}>
                      {busy === c.platform ? <Loader2 size={13} className="animate-spin" /> : <KeyRound size={13} />} {connected || c.configured ? "Manage" : "Set up"}
                    </button>
                  ) : (
                    <button data-testid="connector-connect-button" onClick={() => legacyConnect(c.platform)} disabled={busy === c.platform} className={`inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold disabled:opacity-60 ${connected ? "border border-border bg-secondary text-secondary-foreground hover:bg-muted/50" : "bg-primary text-primary-foreground shadow-orangeGlow"}`}>
                      {busy === c.platform ? <Loader2 size={13} className="animate-spin" /> : connected ? <X size={13} /> : <Check size={13} />} {connected ? "Disconnect" : "Connect"}
                    </button>
                  )}
                  <button data-testid="connector-sync-button" onClick={() => sync(c.platform)} disabled={!connected || busy === c.platform} className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-2 text-xs font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-40"><RefreshCw size={13} /> Sync</button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {wizard && wizRow && wizGuide && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={closeWizard}>
          <div className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-border bg-card p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">Connect {wizard}</h2>
              <button onClick={closeWizard} className="rounded-lg p-1 text-muted-foreground hover:bg-muted/50"><X size={18} /></button>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Credentials are encrypted on the server and stored only for this business. They are never shown again after saving.</p>

            <div className="mt-4 rounded-xl border border-border bg-muted/30 p-4">
              <p className="flex items-center gap-1.5 text-xs font-semibold text-foreground"><ExternalLink size={13} /> 1 · Get your keys (takes a few minutes, free)</p>
              <ol className="mt-2 list-decimal space-y-1 pl-4 text-xs text-muted-foreground">
                {wizGuide.steps.map((s) => <li key={s}>{s}</li>)}
              </ol>
              <a href={wizGuide.link} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline">{wizGuide.linkLabel} <ExternalLink size={11} /></a>
            </div>

            <p className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-foreground"><KeyRound size={13} /> 2 · Paste your credentials</p>
            <div className="mt-2 space-y-3">
              {(wizRow.requires || []).map((key) => (
                <label key={key} className="block">
                  <span className="mb-1 block text-xs font-medium text-muted-foreground">{FIELD_LABELS[key] || key}</span>
                  <input
                    type={key.includes("secret") || key.includes("token") ? "password" : "text"}
                    value={fields[key] || ""}
                    onChange={(e) => setFields({ ...fields, [key]: e.target.value })}
                    placeholder={FIELD_LABELS[key] || key}
                    className="w-full rounded-lg border border-border bg-background/60 px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </label>
              ))}
            </div>

            <div className="mt-4 flex items-center gap-2">
              <button onClick={runTest} disabled={testing || saving} className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-secondary px-3 py-2 text-xs font-semibold text-secondary-foreground hover:bg-muted/50 disabled:opacity-50">
                {testing ? <Loader2 size={13} className="animate-spin" /> : <ShieldCheck size={13} />} Test connection
              </button>
              <button onClick={saveAndConnect} disabled={saving || testing} className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground shadow-orangeGlow hover:opacity-90 disabled:opacity-50">
                {saving ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />} Save & connect
              </button>
              {(wizRow.credentials_stored || wizRow.auth_status === "connected") && (
                <button onClick={() => disconnect(wizard)} disabled={busy === wizard || saving} className="ml-auto inline-flex items-center gap-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs font-semibold text-red-400 hover:bg-red-500/20 disabled:opacity-50">
                  <X size={13} /> Disconnect
                </button>
              )}
            </div>

            {testResult && (
              <div className={`mt-4 rounded-xl border p-3 text-xs ${testResult.ok ? "border-[rgba(34,197,94,0.3)] bg-[rgba(34,197,94,0.1)] text-[hsl(var(--lx-green))]" : "border-red-500/30 bg-red-500/10 text-red-400"}`}>
                <p className="flex items-center gap-1.5 font-semibold">{testResult.ok ? <ShieldCheck size={13} /> : <AlertTriangle size={13} />} {testResult.ok ? "Connection test passed" : "Connection test failed"}</p>
                <p className="mt-1 opacity-90">{testResult.message}</p>
              </div>
            )}

            {wizard === "TradeMe" && wizRow.auth_status === "connected" && (
              <p className="mt-3 flex items-center gap-1.5 text-xs text-[hsl(var(--lx-green))]"><Lock size={12} /> TradeMe is connected. Sync pulls live market anchors and queues approval-gated price suggestions.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
