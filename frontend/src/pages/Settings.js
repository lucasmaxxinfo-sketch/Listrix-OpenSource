import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, Save, ImagePlus, X, Palette, BrainCircuit, Building2, Bell, Users, Shield, Database, Download, Plug, Upload, Trash2, Mail } from "lucide-react";
import { useWorkspace, applyBranding } from "@/context/WorkspaceContext";
import { updateWorkspace, API, getMembers, importCsv, inviteMember, removeMember } from "@/lib/api";
import { compressImage } from "@/lib/utils";

const TABS = [
  { id: "branding", label: "Branding", icon: Palette },
  { id: "ai", label: "AI Preferences", icon: BrainCircuit },
  { id: "business", label: "Business", icon: Building2 },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "team", label: "Team Members", icon: Users },
  { id: "security", label: "Security", icon: Shield },
  { id: "backup", label: "Data & Backup", icon: Database },
];
const input = "w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm outline-none focus:border-primary/50 focus:ring-2 focus:ring-ring/40";

export default function Settings() {
  const { current, setCurrent, refresh } = useWorkspace();
  const [tab, setTab] = useState("branding");
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [members, setMembers] = useState([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [csvText, setCsvText] = useState("");
  const [importResult, setImportResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (current) { getMembers(current.id).then(setMembers).catch(() => setMembers([])); } }, [current]);

  useEffect(() => { if (current) setForm({ ...current, ai_preferences: { ...(current.ai_preferences || {}) } }); }, [current]);
  if (!form) return <div className="flex h-64 items-center justify-center text-muted-foreground"><Loader2 className="animate-spin" size={26} /></div>;

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const setAI = (k) => (e) => setForm({ ...form, ai_preferences: { ...form.ai_preferences, [k]: e.target.value } });

  const onLogo = async (e) => {
    const f = e.target.files?.[0]; if (!f) return;
    if (f.size > 2 * 1024 * 1024) return toast.error("Logo must be under 2MB");
    try {
      const dataUrl = await compressImage(f, { maxDim: 256, quality: 0.82, maxDataUrlChars: 250_000 });
      setForm({ ...form, logo: dataUrl });
    } catch (err) {
      toast.error(err?.message || "Could not process the logo.");
    }
    e.target.value = "";
  };

  const save = async () => {
    setSaving(true);
    try {
      const payload = { name: form.name, logo: form.logo, primary_color: form.primary_color, secondary_color: form.secondary_color,
        contact_email: form.contact_email, contact_phone: form.contact_phone, website: form.website, currency: form.currency,
        timezone: form.timezone, business_type: form.business_type, tax_rate: form.tax_rate === "" ? null : Number(form.tax_rate),
        ai_preferences: form.ai_preferences };
      const updated = await updateWorkspace(current.id, payload);
      setCurrent(updated); applyBranding(updated); await refresh(updated.id);
      toast.success("Settings saved — branding applied");
    } catch { toast.error("Failed to save settings"); } finally { setSaving(false); }
  };

  return (
    <div data-testid="settings-page" className="grid gap-6 lg:grid-cols-[220px_1fr]">
      <nav className="space-y-1">
        {TABS.map((t) => (
          <button key={t.id} data-testid={`settings-tab-${t.id}`} onClick={() => setTab(t.id)} className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-colors ${tab === t.id ? "bg-muted/60 text-foreground" : "text-muted-foreground hover:bg-muted/40"}`}><t.icon size={16} /> {t.label}</button>
        ))}
      </nav>

      <div className="space-y-5">
        {tab === "branding" && (
          <Card title="Branding" desc="Your logo and colours apply across the whole workspace instantly.">
            <div className="flex items-center gap-4">
              {form.logo ? <div className="relative"><img src={form.logo} alt="logo" className="h-16 w-16 rounded-lg border border-border object-cover" /><button onClick={() => setForm({ ...form, logo: null })} className="absolute -right-1.5 -top-1.5 rounded-full bg-black/80 p-1 text-white"><X size={12} /></button></div>
                : <label className="flex h-16 w-16 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border text-muted-foreground hover:border-primary/40"><ImagePlus size={18} /><input type="file" accept="image/*" className="hidden" onChange={onLogo} data-testid="logo-upload" /></label>}
              <div><p className="text-sm font-medium">Business logo</p><p className="text-xs text-muted-foreground">PNG/JPG, under 2MB. Appears in the sidebar & switcher.</p></div>
            </div>
            <Field label="Business name"><input className={input} value={form.name || ""} onChange={set("name")} data-testid="settings-name" /></Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Primary (accent) colour"><div className="flex items-center gap-2"><input type="color" value={form.primary_color || "#FF7A1A"} onChange={set("primary_color")} className="h-10 w-14 rounded-md border border-border bg-transparent" data-testid="settings-primary-color" /><input className={input} value={form.primary_color || ""} onChange={set("primary_color")} /></div></Field>
              <Field label="Secondary colour"><div className="flex items-center gap-2"><input type="color" value={form.secondary_color || "#3B82F6"} onChange={set("secondary_color")} className="h-10 w-14 rounded-md border border-border bg-transparent" /><input className={input} value={form.secondary_color || ""} onChange={set("secondary_color")} /></div></Field>
            </div>
          </Card>
        )}
        {tab === "ai" && (
          <Card title="AI Preferences" desc="The Marketing Intelligence AI adapts to these preferences for this workspace only.">
            <Field label="Preferred writing style"><input className={input} value={form.ai_preferences.writing_style || ""} onChange={setAI("writing_style")} data-testid="settings-writing-style" /></Field>
            <Field label="Pricing behaviour"><input className={input} value={form.ai_preferences.pricing_behavior || ""} onChange={setAI("pricing_behavior")} /></Field>
            <Field label="Selling strategy"><input className={input} value={form.ai_preferences.selling_strategy || ""} onChange={setAI("selling_strategy")} /></Field>
            <Field label="Customer communication style"><input className={input} value={form.ai_preferences.customer_comms_style || ""} onChange={setAI("customer_comms_style")} /></Field>
          </Card>
        )}
        {tab === "business" && (
          <Card title="Business Profile" desc="Contact, currency and tax settings for this workspace.">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Business type"><input className={input} value={form.business_type || ""} onChange={set("business_type")} /></Field>
              <Field label="Website"><input className={input} value={form.website || ""} onChange={set("website")} placeholder="https://" /></Field>
              <Field label="Contact email"><input className={input} value={form.contact_email || ""} onChange={set("contact_email")} /></Field>
              <Field label="Contact phone"><input className={input} value={form.contact_phone || ""} onChange={set("contact_phone")} /></Field>
              <Field label="Currency"><input className={input} value={form.currency || ""} onChange={set("currency")} /></Field>
              <Field label="Timezone"><input className={input} value={form.timezone || ""} onChange={set("timezone")} /></Field>
              <Field label="Tax rate (%)"><input type="number" className={input} value={form.tax_rate ?? ""} onChange={set("tax_rate")} /></Field>
            </div>
          </Card>
        )}
        {tab === "notifications" && <Placeholder icon={Bell} title="Notifications" note="Alert routing (dashboard, inbox, command center) is active. Channel preferences (email/push) are on the roadmap." />}
        {tab === "team" && (
          <Card title="Team Members" desc="Invite collaborators. Only the workspace owner can invite or remove members.">
            <div className="flex gap-2">
              <div className="relative flex-1"><Mail size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" /><input value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} placeholder="member@example.com" className={input + " pl-9"} /></div>
              <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)} className={input + " w-28"}>
                <option value="member">Member</option><option value="viewer">Viewer</option>
              </select>
              <button data-testid="invite-member-button" disabled={busy} onClick={async () => {
                if (!inviteEmail.trim()) return toast.error("Enter an email to invite");
                setBusy(true);
                try { await inviteMember(current.id, { email: inviteEmail.trim(), role: inviteRole }); toast.success("Member invited"); setInviteEmail(""); setMembers(await getMembers(current.id)); } catch (e) { toast.error(e?.response?.data?.detail || "Invite failed"); } finally { setBusy(false); }
              }} className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60"><Users size={15} /> Invite</button>
            </div>
            <div className="space-y-2">
              {members.length === 0 && <p className="rounded-lg border border-dashed border-border p-4 text-center text-xs text-muted-foreground">No members yet — you are the sole operator.</p>}
              {members.map((m) => (
                <div key={m.id} className="flex items-center justify-between rounded-lg border border-border bg-card/60 px-3 py-2.5">
                  <div><p className="text-sm font-medium">{m.email}</p><p className="text-[11px] text-muted-foreground">{m.role} · {m.status}</p></div>
                  <button disabled={busy} onClick={async () => { setBusy(true); try { await removeMember(current.id, m.id); toast.success("Member removed"); setMembers(await getMembers(current.id)); } catch { toast.error("Remove failed"); } finally { setBusy(false); } }} className="rounded-md border border-border p-1.5 text-muted-foreground hover:text-[hsl(var(--destructive))]" aria-label={`Remove ${m.email}`}><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          </Card>
        )}
        {tab === "security" && <Placeholder icon={Shield} title="Security" note="Authentication, audit logging and encrypted secrets are planned. API secrets are stored server-side in environment config." />}
        {tab === "backup" && (
          <>
          <Card title="Data & Backup" desc="Export a full snapshot of this workspace's data.">
            <a data-testid="export-link" href={`${API}/workspaces/${current.id}/export`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong"><Download size={15} /> Export workspace (JSON)</a>
            <p className="text-xs text-muted-foreground">Includes items, listings, suggestions, performance, briefs and events for this workspace only.</p>
          </Card>
          <Card title="Import items (CSV)" desc="Bulk-create items. Columns: name, description, condition, cost, category (name is required; cost must be a number).">
            <textarea value={csvText} onChange={(e) => setCsvText(e.target.value)} rows={6} placeholder={"name,description,condition,cost,category\nSony WH-1000XM4,Wireless headphones,Like New,180,Electronics"} className={"font-mono " + input} />
            <div className="flex items-center gap-3">
              <button data-testid="import-csv-button" disabled={busy || !csvText.trim()} onClick={async () => {
                setBusy(true); setImportResult(null);
                try { const r = await importCsv(csvText); setImportResult(r); toast.success(`Imported ${r.imported} item(s)`); } catch (e) { toast.error(e?.response?.data?.detail || "Import failed"); } finally { setBusy(false); }
              }} className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60"><Upload size={15} /> Import CSV</button>
              {importResult && <p className="text-xs text-muted-foreground">{importResult.imported} imported · {importResult.skipped} skipped</p>}
            </div>
            {importResult?.errors?.length > 0 && <ul className="space-y-1 rounded-lg border border-border bg-card/50 p-3 text-xs text-muted-foreground">{importResult.errors.slice(0, 10).map((e) => <li key={e}>• {e}</li>)}</ul>}
          </Card>
          </>
        )}

        {["branding", "ai", "business"].includes(tab) && (
          <button data-testid="settings-save" onClick={save} disabled={saving} className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-orangeGlow hover:shadow-orangeGlowStrong disabled:opacity-60">{saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />} Save changes</button>
        )}
      </div>
    </div>
  );
}

function Card({ title, desc, children }) {
  return <div className="rounded-xl border border-border bg-card/50 p-6 shadow-panelSoft"><h2 className="text-lg font-bold">{title}</h2>{desc && <p className="mb-4 mt-0.5 text-sm text-muted-foreground">{desc}</p>}<div className="space-y-4">{children}</div></div>;
}
function Field({ label, children }) { return <div><label className="mb-1.5 block text-xs font-medium text-muted-foreground">{label}</label>{children}</div>; }
function Placeholder({ icon: Icon, title, note }) {
  return <div className="rounded-xl border border-border bg-card/50 p-6"><div className="mb-2 flex items-center gap-2"><Icon size={18} className="text-primary" /><h2 className="text-lg font-bold">{title}</h2></div><p className="text-sm text-muted-foreground">{note}</p></div>;
}
